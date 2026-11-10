import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from runtime.github_publisher import GitHubPublisher, snapshot_request
from runtime.publication_gate import PublicationGate
from scripts import publish_review

SHA = "a" * 40
REQUEST = {"kind": "review", "payload": {"commit_id": SHA, "event": "COMMENT", "body": "Finding"}}
PR = {"number": 1, "state": "open", "head": {"sha": SHA},
      "base": {"repo": {"full_name": "owner/repo"}}}
REVIEW = {"id": 42, "commit_id": SHA, "body": "Finding", "state": "COMMENTED",
          "user": {"id": 123, "login": "operator"},
          "submitted_at": "2026-11-10T00:00:00Z",
          "html_url": "https://github.com/owner/repo/pull/1#pullrequestreview-42"}


class PublicationBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.request = copy.deepcopy(REQUEST)
        self.gate = PublicationGate()
        with patch("shutil.which", return_value="/trusted/gh"):
            self.publisher = GitHubPublisher()

    def grant(self):
        self.gate.record_operator_approval("owner/repo", 1, SHA, self.request, account="operator")

    def publish(self, gate, repository, number, sha, request):
        return self.publisher.publish(gate, repository, number, sha, request, account="operator")

    def test_missing_or_forged_approval_never_reaches_post(self):
        for request in [self.request, {**self.request, "user_confirmed": True}]:
            with self.subTest(request=request), patch.object(self.publisher, "_api", return_value=PR) as api:
                with self.assertRaises((PermissionError, ValueError)):
                    self.publish(self.gate, "owner/repo", 1, SHA, request)
                self.assertFalse(any(c.args[0] == "POST" for c in api.call_args_list))

    def test_real_dispatch_consumes_grant_and_reads_submitted_review_back(self):
        self.grant()
        with patch.object(self.publisher, "_api", side_effect=[REVIEW["user"], PR, REVIEW, REVIEW, [], REVIEW["user"], PR]) as api:
            self.assertEqual(self.publish(self.gate, "owner/repo", 1, SHA, self.request), REVIEW)
            with self.assertRaises(PermissionError):
                self.publish(self.gate, "owner/repo", 1, SHA, self.request)
        self.assertEqual([c.args[:2] for c in api.call_args_list], [
            ("GET", "user"),
            ("GET", "repos/owner/repo/pulls/1"),
            ("POST", "repos/owner/repo/pulls/1/reviews"),
            ("GET", "repos/owner/repo/pulls/1/reviews/42"),
            ("GET", "repos/owner/repo/pulls/1/reviews/42/comments?per_page=100&page=1"),
            ("GET", "user"),
            ("GET", "repos/owner/repo/pulls/1")])

    def test_head_target_payload_and_endpoint_changes_prevent_writes(self):
        changed_head = copy.deepcopy(PR)
        changed_head["head"]["sha"] = "b" * 40
        renamed = copy.deepcopy(PR)
        renamed["base"]["repo"]["full_name"] = "other/repo"
        changed_body = copy.deepcopy(self.request)
        changed_body["payload"]["body"] = "Changed"
        file_request = {"kind": "comment", "payload": {"commit_id": SHA, "body": "Finding",
                                                       "path": "a.py", "subject_type": "file"}}
        for repository, number, request, pr in [
            ("owner/repo", 1, self.request, changed_head),
            ("owner/repo", 1, self.request, renamed),
            ("other/repo", 1, self.request, PR),
            ("owner/repo", 2, self.request, PR),
            ("owner/repo", 1, changed_body, PR),
            ("owner/repo", 1, file_request, PR),
        ]:
            self.grant()
            with self.subTest(repository=repository, request=request), patch.object(self.publisher, "_api", side_effect=[REVIEW["user"], pr]) as api:
                with self.assertRaises(PermissionError):
                    self.publish(self.gate, repository, number, SHA, request)
                self.assertFalse(any(c.args[0] == "POST" for c in api.call_args_list))

    def test_input_mutation_during_head_lookup_cannot_change_frozen_write(self):
        self.grant()
        def api(method, endpoint, payload=None):
            if endpoint == "user":
                return REVIEW["user"]
            if "/comments?" in endpoint:
                return []
            if endpoint.endswith("pulls/1"):
                self.request["payload"]["body"] = "Injected during I/O"
                return PR
            if method == "POST":
                self.assertEqual(payload["body"], "Finding")
            return REVIEW
        with patch.object(self.publisher, "_api", side_effect=api):
            self.publish(self.gate, "owner/repo", 1, SHA, self.request)

    def test_pending_review_and_failed_post_never_retry_or_fallback(self):
        for outcome in [OSError("ambiguous"), {**REVIEW, "state": "PENDING", "submitted_at": None}]:
            self.grant()
            with patch.object(self.publisher, "_api", side_effect=[REVIEW["user"], PR, outcome, outcome]) as api:
                with self.assertRaises((OSError, ValueError)):
                    self.publish(self.gate, "owner/repo", 1, SHA, self.request)
                self.assertEqual(sum(c.args[0] == "POST" for c in api.call_args_list), 1)
            with self.assertRaises(PermissionError):
                self.gate.consume("owner/repo", 1, SHA, self.request, account="operator")

    def test_file_comment_uses_review_comment_endpoint_not_issue_comment(self):
        request = {"kind": "comment", "payload": {"commit_id": SHA, "path": "a.py",
                                                   "body": "Finding", "subject_type": "file"}}
        result = {**REVIEW, "path": "a.py", "subject_type": "file",
                  "html_url": "https://github.com/owner/repo/pull/1#discussion_r42"}
        self.gate.record_operator_approval("owner/repo", 1, SHA, request, account="operator")
        with patch.object(self.publisher, "_api", side_effect=[REVIEW["user"], PR, result, result]) as api:
            self.publish(self.gate, "owner/repo", 1, SHA, request)
        self.assertEqual(api.call_args_list[2].args[:2], ("POST", "repos/owner/repo/pulls/1/comments"))
        self.assertEqual(api.call_args_list[3].args[:2], ("GET", "repos/owner/repo/pulls/comments/42"))

    def test_unexpected_endpoint_fields_and_commits_fail_before_io(self):
        for request in [{"kind": "issue", "payload": {}},
                        {"kind": "review", "payload": {"commit_id": "b" * 40, "event": "COMMENT"}},
                        {"kind": "review", "payload": {"commit_id": SHA, "event": "PENDING"}},
                        {"kind": "review", "payload": {**REQUEST["payload"], "url": "https://evil.invalid"}}]:
            with self.subTest(request=request), patch.object(self.publisher, "_api") as api:
                with self.assertRaises(ValueError):
                    self.publish(self.gate, "owner/repo", 1, SHA, request)
                api.assert_not_called()

    def test_actual_account_mismatch_never_posts(self):
        for identity in [{"id": 456, "login": "other"}, {"id": None, "login": "operator"}]:
            self.grant()
            with patch.object(self.publisher, "_api", return_value=identity) as api:
                with self.assertRaises(PermissionError):
                    self.publish(self.gate, "owner/repo", 1, SHA, self.request)
                self.assertFalse(any(c.args[0] == "POST" for c in api.call_args_list))

    def test_wrong_readback_author_state_commit_body_or_target_fails(self):
        for changed in [{"user": {"id": 456, "login": "operator"}},
                        {"user": {"id": 123, "login": "other"}},
                        {"commit_id": "b" * 40}, {"body": "Changed"},
                        {"html_url": "https://github.com/owner/repo/pull/2#pullrequestreview-42"},
                        {"html_url": "https://github.com/owner/repo/pull/1#pullrequestreview-99"}]:
            self.grant()
            with self.subTest(changed=changed), patch.object(self.publisher, "_api", side_effect=[
                    REVIEW["user"], PR, REVIEW, {**REVIEW, **changed}]) as api:
                with self.assertRaises(ValueError):
                    self.publish(self.gate, "owner/repo", 1, SHA, self.request)
                self.assertEqual(sum(c.args[0] == "POST" for c in api.call_args_list), 1)
            with self.assertRaises(PermissionError):
                self.gate.consume("owner/repo", 1, SHA, self.request, account="operator")

    def test_inline_review_fetches_full_payload_and_rejects_missing_extra_or_changed_comments(self):
        inline = {"body": "Inline", "path": "code.py", "line": 3, "side": "RIGHT"}
        self.request["payload"]["comments"] = [inline]
        returned = {**inline, "id": 43, "user": REVIEW["user"], "commit_id": SHA, "pull_request_review_id": 42}
        for comments, succeeds in [([returned], True), ([], False), ([returned, returned], False),
                                  ([{**returned, "body": "Changed"}], False),
                                  ([{**returned, "path": "other.py"}], False),
                                  ([{**returned, "line": 4}], False),
                                  ([{**returned, "side": "LEFT"}], False),
                                  ([{**returned, "start_line": 1}], False),
                                  ([{**returned, "commit_id": "b" * 40}], False),
                                  ([{**returned, "pull_request_review_id": 99}], False),
                                  ([{**returned, "user": {"id": 456, "login": "other"}}], False)]:
            self.grant()
            with self.subTest(comments=comments), patch.object(self.publisher, "_api", side_effect=[
                    REVIEW["user"], PR, REVIEW, REVIEW, [{"id": c["id"]} for c in comments], *comments]) as api:
                if succeeds:
                    self.publish(self.gate, "owner/repo", 1, SHA, self.request)
                else:
                    with self.assertRaises(ValueError):
                        self.publish(self.gate, "owner/repo", 1, SHA, self.request)
                self.assertEqual(sum(c.args[0] == "POST" for c in api.call_args_list), 1)

    def test_inline_readback_checks_every_page_and_preserves_duplicate_counts(self):
        inline = {"body": "Inline", "path": "code.py", "line": 3, "side": "RIGHT"}
        self.request["payload"]["comments"] = [inline] * 101
        returned = {**inline, "user": REVIEW["user"], "commit_id": SHA, "pull_request_review_id": 42}
        comments = [{**returned, "id": number} for number in range(1, 102)]
        self.grant()
        with patch.object(self.publisher, "_api", side_effect=[
                REVIEW["user"], PR, REVIEW, REVIEW, [{"id": c["id"]} for c in comments[:100]],
                *comments[:100], [{"id": 101}], comments[100]]) as api:
            self.publish(self.gate, "owner/repo", 1, SHA, self.request)
        self.assertEqual(sum("/comments?" in c.args[1] for c in api.call_args_list), 2)

    def test_cli_cannot_get_consent_from_request_file_or_standard_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            request_file = Path(temporary) / "request.json"
            request_file.write_text(json.dumps(REQUEST))
            with patch("builtins.open", side_effect=OSError("no operator terminal")), \
                 patch.object(publish_review, "GitHubPublisher") as publisher, \
                 patch("sys.stdin", io.StringIO("yes\n")), patch("sys.stderr", io.StringIO()):
                self.assertEqual(publish_review.main(["--account", "operator", "--repository", "owner/repo", "--pull-number", "1",
                                                      "--reviewed-sha", SHA, "--request", str(request_file)]), 1)
                publisher.assert_not_called()

    def test_actual_subprocess_dispatch_has_fixed_host_endpoint_and_exact_json(self):
        # A local executable stub, not a live GitHub or prompt-injection test.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capture = root / "calls.jsonl"
            stub = root / "gh"
            stub.write_text(f"#!{sys.executable}\n" +
                "import sys,json,os\n"
                "data=sys.stdin.read() if '--input' in sys.argv else None\n"
                "with open(os.environ['TEST_GH_CAPTURE'],'a') as f: f.write(json.dumps({'argv':sys.argv[1:],'data':data,'environment_marker':os.environ.get('TEST_FROZEN_ENV')})+'\\n')\n"
                f"pr={PR!r}\nreview={REVIEW!r}\n"
                "endpoint=sys.argv[sys.argv.index('--method')+2]\n"
                "print(json.dumps(review['user'] if endpoint=='user' else [] if '/comments?' in endpoint else pr if endpoint.endswith('pulls/1') else review))\n")
            stub.chmod(0o755)
            with patch("shutil.which", return_value=str(stub)), patch.dict(os.environ, {"TEST_GH_CAPTURE": str(capture), "GH_HOST": "evil.invalid", "TEST_FROZEN_ENV": "original"}):
                publisher = GitHubPublisher()
                os.environ["TEST_FROZEN_ENV"] = "changed after publisher construction"
                self.grant()
                publisher.publish(self.gate, "owner/repo", 1, SHA, self.request, account="operator")
                with self.assertRaises(PermissionError):
                    publisher.publish(self.gate, "owner/repo", 1, SHA, self.request, account="operator")
            calls = [json.loads(line) for line in capture.read_text().splitlines()]
            writes = [call for call in calls if "POST" in call["argv"]]
            self.assertEqual(len(writes), 1)
            self.assertEqual(writes[0]["argv"][1:5], ["--hostname", "github.com", "--method", "POST"])
            self.assertEqual(json.loads(writes[0]["data"]), REQUEST["payload"])
            self.assertTrue(all(call["environment_marker"] == "original" for call in calls))
