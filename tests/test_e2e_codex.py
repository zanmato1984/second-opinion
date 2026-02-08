import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(cmd, cwd, env=None):
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


class CodexE2ETest(unittest.TestCase):
    @unittest.skipUnless(
        os.environ.get("CODEX_E2E") == "1",
        "Set CODEX_E2E=1 to enable Codex end-to-end tests.",
    )
    def test_codex_runs_second_opinion_skill(self):
        codex_cmd = os.environ.get("CODEX_E2E_CMD", "codex")
        if shutil.which(codex_cmd) is None:
            self.skipTest(f"Codex CLI not found: {codex_cmd}")
        if shutil.which("git") is None:
            self.skipTest("git not found")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            codex_home = tmp_path / "codex_home"
            skill_dst = codex_home / "skills" / "second-opinion"
            skill_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(
                REPO_ROOT,
                skill_dst,
                ignore=shutil.ignore_patterns(".git", "__pycache__"),
            )

            repo = tmp_path / "workspace"
            repo.mkdir()
            _run(["git", "init"], cwd=repo)
            _run(["git", "config", "user.email", "codex@example.com"], cwd=repo)
            _run(["git", "config", "user.name", "Codex"], cwd=repo)

            sample_file = repo / "main.go"
            sample_file.write_text(
                "package main\n\nfunc add(a, b int) int { return a + b }\n",
                encoding="utf-8",
            )
            _run(["git", "add", "main.go"], cwd=repo)
            _run(["git", "commit", "-m", "init"], cwd=repo)

            sample_file.write_text(
                "package main\n\nfunc add(a, b int) int { return a + b }\n\nfunc sub(a, b int) int { return a - b }\n",
                encoding="utf-8",
            )

            prompt = (
                "Give second opinion on this change. "
                "Run the Second Opinion review workflow and write review.md and review.json in the repo root."
            )

            cmd = [
                codex_cmd,
                "-C",
                str(repo),
                "-s",
                "workspace-write",
                "-a",
                "never",
            ]
            model = os.environ.get("CODEX_E2E_MODEL")
            if model:
                cmd.extend(["-m", model])
            cmd.extend(["review", "--uncommitted", prompt])

            env = os.environ.copy()
            env["CODEX_HOME"] = str(codex_home)
            timeout = int(os.environ.get("CODEX_E2E_TIMEOUT", "600"))
            result = subprocess.run(
                cmd,
                cwd=repo,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            )
            if result.returncode != 0:
                raise AssertionError(
                    f"codex review failed (exit {result.returncode})\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
                )

            review_md = repo / "review.md"
            review_json = repo / "review.json"
            self.assertTrue(review_md.is_file(), "review.md not created")
            self.assertTrue(review_json.is_file(), "review.json not created")

            with review_json.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            self.assertIn("findings", data, "review.json missing findings")
            self.assertIsInstance(data["findings"], list, "findings must be a list")

