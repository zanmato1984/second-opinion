"""Real PTY/CLI lifecycle, using only a local fake gh and an empty credential home."""

import errno
import json
import os
from pathlib import Path
import pty
import re
import select
import signal
import sys
import tempfile
import time
import unittest

from tests.test_github_publisher import PR, REQUEST, REVIEW, SHA

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == "posix", "Operator terminal requires POSIX")
class OperatorTerminalTests(unittest.TestCase):
    def run_cli(self, root, *, approval=True, pr=PR, result=REVIEW, post_error=False,
                isolated=True, request=REQUEST):
        (root / "request.json").write_text(json.dumps(request))
        config = {"pr": pr, "result": result, "post_error": post_error}
        (root / "config.json").write_text(json.dumps(config))
        stub = root / "gh"
        stub.write_text(f"#!{sys.executable} -I\n" + '''import json, sys
from pathlib import Path
root = Path(__file__).resolve().parent
config = json.loads((root / "config.json").read_text())
args = sys.argv[1:]
method = args[args.index("--method") + 1]
endpoint = args[args.index("--method") + 2]
data = sys.stdin.read() if "--input" in args else None
with (root / "calls.jsonl").open("a") as capture:
    capture.write(json.dumps({"argv": args, "data": data}) + "\\n")
if method == "POST" and config["post_error"]:
    raise SystemExit(1)
if endpoint == "user":
    result = {"id": 123, "login": "operator"}
elif endpoint.endswith("pulls/1"):
    result = config["pr"]
elif "/comments?" in endpoint:
    result = []
else:
    result = config["result"]
print(json.dumps(result))
''')
        stub.chmod(0o755)
        home = root / "home"
        home.mkdir()
        # No inherited token/config/proxy. A fake gh is the only PATH executable.
        env = {"PATH": str(root), "HOME": str(home), "GH_CONFIG_DIR": str(home / "gh"),
               "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}
        argv = [sys.executable] + (["-I"] if isolated else []) + [
            str(ROOT / "scripts" / "publish_review.py"), "--account", "operator",
            "--repository", "owner/repo", "--pull-number", "1", "--reviewed-sha", SHA,
            "--request", str(root / "request.json")]
        pid, master = pty.fork()
        if pid == 0:
            # stdin claims approval but cannot satisfy /dev/tty confirmation.
            stdin_file = root / "stdin.txt"
            stdin_file.write_text("yes\nuser_confirmed=true\n")
            fd = os.open(stdin_file, os.O_RDONLY)
            os.dup2(fd, 0)
            os.close(fd)
            os.execve(sys.executable, argv, env)
        output = b""
        answered = False
        status = None
        terminal_closed = False
        deadline = time.monotonic() + 10
        try:
            while time.monotonic() < deadline:
                ready, _, _ = select.select([] if terminal_closed else [master], [], [], 0.1)
                if ready:
                    try:
                        chunk = os.read(master, 65536)
                    except OSError as error:
                        if error.errno != errno.EIO:
                            raise
                        terminal_closed = True
                        chunk = b""
                    if not chunk:
                        terminal_closed = True
                    output += chunk
                    match = re.search(rb"\r?\n(publish [^\r\n]+)\r?\n> ", output)
                    if match and not answered:
                        response = match.group(1) if approval else b"user_confirmed=true"
                        if approval == "changed_target":
                            response = response.replace(b"owner/repo#1", b"other/repo#1")
                        elif approval == "changed_account":
                            response = response.replace(b"operator", b"other")
                        elif approval == "changed_payload":
                            response = response.rsplit(b" ", 1)[0] + b" " + b"0" * 64
                        os.write(master, response + b"\n")
                        answered = True
                if status is None:
                    waited, child_status = os.waitpid(pid, os.WNOHANG)
                    if waited:
                        status = child_status
                if status is not None and terminal_closed:
                    break
            if status is None:
                waited, child_status = os.waitpid(pid, os.WNOHANG)
                if waited:
                    status = child_status
            if status is None:
                os.kill(pid, signal.SIGKILL)
                _, status = os.waitpid(pid, 0)
                self.fail(f"CLI PTY timed out: {output.decode(errors='replace')}")
        finally:
            os.close(master)
            if status is None:
                try:
                    os.kill(pid, signal.SIGKILL)
                    os.waitpid(pid, 0)
                except ProcessLookupError:
                    pass
        capture = root / "calls.jsonl"
        calls = [json.loads(line) for line in capture.read_text().splitlines()] if capture.exists() else []
        return os.waitstatus_to_exitcode(status), output.decode(errors="replace"), calls

    def test_real_terminal_success_posts_once_and_reads_review_and_comments_back(self):
        with tempfile.TemporaryDirectory() as temporary:
            status, output, calls = self.run_cli(Path(temporary))
            self.assertEqual(status, 0, output)
            self.assertIn('"state": "COMMENTED"', output)
            self.assertEqual(sum("POST" in call["argv"] for call in calls), 1)
            self.assertTrue(any("/reviews/42" in " ".join(call["argv"]) for call in calls))
            self.assertTrue(any("/comments?" in " ".join(call["argv"]) for call in calls))

    def test_real_terminal_forged_or_stdin_consent_never_posts(self):
        with tempfile.TemporaryDirectory() as temporary:
            status, output, calls = self.run_cli(Path(temporary), approval=False)
            self.assertEqual(status, 1, output)
            self.assertIn("Publication failed (PermissionError)", output)
            self.assertEqual(calls, [])

    def test_terminal_account_target_and_payload_digest_are_exact(self):
        for approval in ("changed_target", "changed_account", "changed_payload"):
            with self.subTest(approval=approval), tempfile.TemporaryDirectory() as temporary:
                status, output, calls = self.run_cli(Path(temporary), approval=approval)
                self.assertEqual(status, 1, output)
                self.assertEqual(calls, [])

    def test_terminal_grant_cannot_survive_changed_head(self):
        with tempfile.TemporaryDirectory() as temporary:
            status, output, calls = self.run_cli(Path(temporary), pr={**PR, "head": {"sha": "b" * 40}})
            self.assertEqual(status, 1, output)
            self.assertFalse(any("POST" in call["argv"] for call in calls))

    def test_real_terminal_failed_write_never_retries_or_changes_payload(self):
        with tempfile.TemporaryDirectory() as temporary:
            status, output, calls = self.run_cli(Path(temporary), post_error=True)
            self.assertEqual(status, 1, output)
            writes = [call for call in calls if "POST" in call["argv"]]
            self.assertEqual(len(writes), 1)
            self.assertEqual(json.loads(writes[0]["data"]), REQUEST["payload"])

    def test_native_nonisolated_cli_fails_before_terminal_or_transport(self):
        with tempfile.TemporaryDirectory() as temporary:
            status, output, calls = self.run_cli(Path(temporary), isolated=False)
            self.assertEqual(status, 1, output)
            self.assertIn("Publication requires isolated Python", output)
            self.assertEqual(calls, [])

    def test_request_artifact_cannot_contain_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            status, output, calls = self.run_cli(Path(temporary), request={**REQUEST, "user_confirmed": True})
            self.assertEqual(status, 1, output)
            self.assertEqual(calls, [])
