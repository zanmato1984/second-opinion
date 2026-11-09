"""Optional real-CLI regressions; loopback fixture only, never a model/API call."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

from tests import e2e_helpers as helpers


@unittest.skipUnless(os.environ.get("CODEX_OFFLINE_CLI") == "1",
                     "Set CODEX_OFFLINE_CLI=1 for installed-CLI loopback tests (no live API).")
class OfflineCodexTests(unittest.TestCase):
    def test_default_provider_auth_and_isolated_shell_environment(self):
        codex = shutil.which("codex")
        if not codex or not Path("/bin/sh").is_file():
            self.skipTest("Requires Codex CLI and /bin/sh")
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name).resolve()
        repo = root / "workspace"
        repo.mkdir()
        subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
        home = root / "codex"
        helpers._write_config(home)
        isolated_home = root / "home"
        isolated_home.mkdir()
        requests = []
        synthetic_key = "offline-synthetic-dedicated-key"

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"models":[]}')

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests.append((self.path, self.headers.get("Authorization"), body))
                response_id = f"resp_{len(requests)}"
                events = [{"type": "response.created", "response": {"id": response_id}}]
                if len(requests) == 1:
                    command = (
                        'printf "%s\\n" "$HOME" > shell-home.txt; '
                        'printf "%s\\n" "${CODEX_API_KEY-unset}" > shell-key.txt; '
                        'printf "%s\\n" "${OPENAI_API_KEY-unset}" > shell-openai-key.txt'
                    )
                    tools = {tool.get("name") for tool in body["tools"]}
                    if "exec_command" in tools:
                        name, arguments = "exec_command", {"cmd": command, "yield_time_ms": 1000,
                                                           "shell": "/bin/sh", "login": False}
                        events.append({"type": "response.output_item.done", "item": {
                            "type": "function_call", "call_id": "call_shell", "name": name,
                            "arguments": json.dumps(arguments)}})
                else:
                    events.append({"type": "response.output_item.done", "item": {
                        "type": "message", "role": "assistant", "id": "message_done",
                        "content": [{"type": "output_text", "text": "offline fixture done"}]}})
                events.append({"type": "response.completed", "response": {"id": response_id,
                    "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}}})
                data = "".join(f'event: {event["type"]}\ndata: {json.dumps(event)}\n\n'
                               for event in events).encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        config = home / "config.toml"
        config.write_text(
            f'openai_base_url = "http://127.0.0.1:{server.server_port}/v1"\n'
            'model = "gpt-5.1-codex-mini"\nweb_search = "disabled"\n'
            + config.read_text().replace('[features]', '[features]\nresponses_websockets = false\n'
                                         'responses_websockets_v2 = false')
        )
        # Only the built-in OpenAI endpoint changes: no custom provider/env_key
        # may mask a broken default-provider auth variable. A non-login /bin/sh
        # probe never reads personal startup files even if HOME is lost. This
        # does not add a bypass of Codex's own workspace-write sandbox.
        with patch.dict(os.environ, {"CODEX_E2E_TIMEOUT": "30"}, clear=True):
            helpers.codex_exec(codex, repo, home, "Run the offline fixture shell.", synthetic_key)
        self.assertEqual(len(requests), 2)
        self.assertIn("exec_command", {tool.get("name") for tool in requests[0][2]["tools"]})
        for path, auth, body in requests:
            self.assertEqual(path, "/v1/responses")
            self.assertEqual(auth, f"Bearer {synthetic_key}")
            self.assertNotIn(synthetic_key, json.dumps(body))
        self.assertFalse((home / "auth.json").exists())
        self.assertFalse(list((home / "shell_snapshots").glob("*")))
        self.assertEqual((repo / "shell-home.txt").read_text().strip(), str(isolated_home))
        self.assertEqual((repo / "shell-key.txt").read_text().strip(), "unset")
        self.assertEqual((repo / "shell-openai-key.txt").read_text().strip(), "unset")
