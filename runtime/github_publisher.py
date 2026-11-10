"""Trusted host GitHub dispatcher. Never expose this module as a model tool."""

import json
import os
from pathlib import Path
import shutil
import subprocess

from runtime.publication_gate import _binding


def snapshot_request(repository, pull_number, reviewed_sha, request):
    """Freeze the exact endpoint choice and wire payload before approval/I/O."""
    _binding(repository, pull_number, reviewed_sha, request)
    frozen = json.loads(json.dumps(request, allow_nan=False))
    if set(frozen) != {"kind", "payload"} or frozen["kind"] not in ("review", "comment"):
        raise ValueError("Expected a review or review-comment request")
    payload = frozen["payload"]
    if not isinstance(payload, dict) or payload.get("commit_id") != reviewed_sha.lower():
        raise ValueError("Payload must name the full reviewed commit")
    if frozen["kind"] == "review":
        if set(payload) - {"commit_id", "event", "body", "comments"}:
            raise ValueError("Unexpected review field")
        if payload.get("event") not in ("COMMENT", "APPROVE", "REQUEST_CHANGES"):
            raise ValueError("A submitted review event is required")
        if "body" in payload and not isinstance(payload["body"], str):
            raise ValueError("Expected review body text")
        comments = payload.get("comments", [])
        if not isinstance(comments, list):
            raise ValueError("Expected inline comments")
        for comment in comments:
            _validate_comment(comment, inline_only=True)
    else:
        _validate_comment({k: v for k, v in payload.items() if k != "commit_id"})
    return frozen


def _validate_comment(comment, inline_only=False):
    if not isinstance(comment, dict) or set(comment) - {"body", "path", "line", "side", "subject_type"}:
        raise ValueError("Unexpected review comment field")
    if not isinstance(comment.get("body"), str) or not comment["body"].strip():
        raise ValueError("Expected comment body")
    path = comment.get("path")
    if not isinstance(path, str) or not path or path.startswith("/") or ".." in path.split("/"):
        raise ValueError("Expected a repository-relative comment path")
    if comment.get("subject_type") == "file" and not inline_only:
        if "line" in comment or "side" in comment:
            raise ValueError("File comments must not have line anchors")
    elif (type(comment.get("line")) is not int or comment["line"] < 1
          or comment.get("side") != "RIGHT" or "subject_type" in comment):
        raise ValueError("Expected a RIGHT-side inline anchor")


class GitHubPublisher:
    """A real gh write boundary, called only by authenticated trusted host code.

    Approval never comes from request JSON. Callers supply a separate in-memory
    PublicationGate granted through their authenticated operator event handler.
    No fallback, automatic retry, shell command, or arbitrary endpoint is exposed.
    """

    def __init__(self):
        executable = shutil.which("gh")
        if not executable:
            raise OSError("gh is unavailable")
        self.executable = str(Path(executable).resolve())

    def _api(self, method, endpoint, payload=None):
        argv = [self.executable, "api", "--hostname", "github.com", "--method", method,
                endpoint, "-H", "Accept: application/vnd.github+json"]
        if payload is not None:
            argv.extend(["--input", "-"])
        result = subprocess.run(
            argv, input=json.dumps(payload, allow_nan=False) if payload is not None else None,
            text=True, capture_output=True, check=False, timeout=60,
            cwd=Path(__file__).resolve().parents[1],
            env={**os.environ, "GH_HOST": "github.com", "GH_PROMPT_DISABLED": "1"})
        if result.returncode:
            # stderr can contain remote/model text or credential-bearing URLs.
            raise OSError("GitHub request failed; inspect remote state before retrying a write")
        return json.loads(result.stdout)

    def publish(self, gate, repository, pull_number, reviewed_sha, request):
        try:
            frozen = snapshot_request(repository, pull_number, reviewed_sha, request)
            prefix = f"repos/{repository.lower()}/pulls/{pull_number}"
            current = self._api("GET", prefix)
            if (current.get("state") != "open" or current.get("number") != pull_number
                    or current.get("base", {}).get("repo", {}).get("full_name", "").lower() != repository.lower()):
                raise PermissionError("PR target changed or is not open")
            head = current["head"]["sha"]
            gate.consume(repository, pull_number, head, frozen)
            suffix = "reviews" if frozen["kind"] == "review" else "comments"
            # The only mutation sink. No model code or callback runs between
            # the one-use check and dispatch of the already frozen payload.
            result = self._api("POST", f"{prefix}/{suffix}", frozen["payload"])
            identifier = result.get("id")
            if type(identifier) is not int or identifier <= 0:
                raise ValueError("Write result is unverified; do not automatically retry")
            detail_path = (f"{prefix}/reviews/{identifier}" if suffix == "reviews" else
                           f"repos/{repository.lower()}/pulls/comments/{identifier}")
            confirmed = self._api("GET", detail_path)
            payload = frozen["payload"]
            if confirmed.get("commit_id") != reviewed_sha.lower():
                raise ValueError("Published commit is unverified")
            expected_url = f"https://github.com/{repository.lower()}/pull/{pull_number}#"
            if not str(confirmed.get("html_url", "")).lower().startswith(expected_url):
                raise ValueError("Published target is unverified")
            if confirmed.get("body", "") != payload.get("body", ""):
                raise ValueError("Published body is unverified")
            if suffix == "reviews":
                state = {"COMMENT": "COMMENTED", "APPROVE": "APPROVED",
                         "REQUEST_CHANGES": "CHANGES_REQUESTED"}[payload["event"]]
                if confirmed.get("state") != state or not confirmed.get("submitted_at"):
                    raise ValueError("Submitted review state is unverified")
            else:
                for key in ("path", "subject_type", "line", "side"):
                    if key in payload and confirmed.get(key) != payload[key]:
                        raise ValueError("Published anchor is unverified")
            return confirmed
        except Exception:
            gate.revoke()
            raise
