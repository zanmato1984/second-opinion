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


def _require_tool(name):
    if shutil.which(name) is None:
        raise unittest.SkipTest(f"Required tool not found: {name}")

def _ensure_auth(codex_home):
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"]
    auth_src = Path(
        os.environ.get(
            "CODEX_E2E_AUTH_SOURCE",
            Path.home() / ".codex" / "auth.json",
        )
    )
    if auth_src.is_file():
        codex_home.mkdir(parents=True, exist_ok=True)
        dst = codex_home / "auth.json"
        shutil.copy2(auth_src, dst)
        try:
            payload = json.loads(auth_src.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AssertionError(f"Invalid auth.json: {auth_src}") from exc
        key = payload.get("OPENAI_API_KEY")
        if not key:
            raise AssertionError(f"auth.json missing OPENAI_API_KEY: {auth_src}")
        return key
    raise AssertionError(
        "Codex auth not found. Run `codex login`, set OPENAI_API_KEY, or set "
        "CODEX_E2E_AUTH_SOURCE to a valid auth.json."
    )


def _copy_config(codex_home):
    config_src = Path(
        os.environ.get(
            "CODEX_E2E_CONFIG_SOURCE",
            Path.home() / ".codex" / "config.toml",
        )
    )
    if config_src.is_file():
        codex_home.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config_src, codex_home / "config.toml")


def _codex_exec(codex_cmd, repo, codex_home, prompt, auth_key):
    cmd = [
        codex_cmd,
        "-C",
        str(repo),
        "-s",
        "workspace-write",
        "--dangerously-bypass-approvals-and-sandbox",
    ]
    model = os.environ.get("CODEX_E2E_MODEL")
    if model:
        cmd.extend(["-m", model])
    cmd.extend(["exec", prompt])

    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    if auth_key and not env.get("OPENAI_API_KEY"):
        env["OPENAI_API_KEY"] = auth_key
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
            f"codex exec failed (exit {result.returncode})\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


@unittest.skipUnless(
    os.environ.get("CODEX_E2E") == "1",
    "Set CODEX_E2E=1 to enable Codex end-to-end tests.",
)
class CodexE2ETest(unittest.TestCase):
    def _prepare_workspace(self):
        codex_cmd = os.environ.get("CODEX_E2E_CMD", "codex")
        _require_tool(codex_cmd)
        _require_tool("git")

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        tmp_path = Path(tmp.name)

        codex_home = tmp_path / "codex_home"
        auth_key = _ensure_auth(codex_home)
        _copy_config(codex_home)
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

        diff = _run(["git", "diff"], cwd=repo).stdout
        if not diff.strip():
            raise AssertionError("git diff returned empty output")
        diff_path = repo / "change.diff"
        diff_path.write_text(diff, encoding="utf-8")

        return codex_cmd, codex_home, repo, diff_path, auth_key

    def test_codex_runs_second_opinion_skill(self):
        codex_cmd, codex_home, repo, _diff_path, auth_key = self._prepare_workspace()

        prompt = (
            "Give second opinion on this change. "
            "Run the Second Opinion review workflow and write review.md and review.json in the repo root."
        )
        _codex_exec(codex_cmd, repo, codex_home, prompt, auth_key)

        review_md = repo / "review.md"
        review_json = repo / "review.json"
        self.assertTrue(review_md.is_file(), "review.md not created")
        self.assertTrue(review_json.is_file(), "review.json not created")

        with review_json.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertIn("findings", data, "review.json missing findings")
        self.assertIsInstance(data["findings"], list, "findings must be a list")

    def test_codex_tagger_stage(self):
        codex_cmd, codex_home, repo, diff_path, auth_key = self._prepare_workspace()

        prompt = (
            "Give second opinion on this change. Run the tagger stage only. "
            f"Use prompts/tagger.prompt with diff at {diff_path.name} and write tagger.json in the repo root."
        )
        _codex_exec(codex_cmd, repo, codex_home, prompt, auth_key)

        tagger_json = repo / "tagger.json"
        self.assertTrue(tagger_json.is_file(), "tagger.json not created")
        with tagger_json.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertIn("signals", data, "tagger.json missing signals")
        self.assertIn("tags", data, "tagger.json missing tags")
        self.assertIsInstance(data["signals"], list, "signals must be a list")
        self.assertIsInstance(data["tags"], list, "tags must be a list")

    def test_codex_compiler_stage(self):
        codex_cmd, codex_home, repo, diff_path, auth_key = self._prepare_workspace()

        tagger_payload = {
            "signals": [{"evidence": "main.go", "reason": "sample change"}],
            "tags": [
                {"tag": "lang:go", "why": "Go source"},
                {"tag": "scope:tidb", "why": "sample scope"},
                {"tag": "risk:concurrency", "why": "sample risk"},
            ],
        }
        tagger_json = repo / "tagger.json"
        tagger_json.write_text(json.dumps(tagger_payload, indent=2), encoding="utf-8")

        prompt = (
            "Give second opinion on this change. Run the compiler stage only. "
            "Read prompts/compiler.prompt. Use tagger.json for derived tags, reviewers/* for metadata and criteria, "
            f"and write compiler.json in the repo root. The diff is at {diff_path.name}."
        )
        _codex_exec(codex_cmd, repo, codex_home, prompt, auth_key)

        compiler_json = repo / "compiler.json"
        self.assertTrue(compiler_json.is_file(), "compiler.json not created")
        with compiler_json.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        for field in [
            "selected_reviewers",
            "rules_used",
            "process_reviewers",
            "compiled_prompt",
            "provenance",
        ]:
            self.assertIn(field, data, f"compiler.json missing {field}")

    def test_codex_reviewer_stage(self):
        codex_cmd, codex_home, repo, diff_path, auth_key = self._prepare_workspace()

        compiler_payload = {
            "selected_reviewers": ["alice"],
            "rules_used": {"alice": ["ALICE-CONCURRENCY-001"]},
            "process_reviewers": [],
            "compiled_prompt": (
                "You are the review stage. Use the diff to produce review.md and review.json. "
                "review.json must include a findings array."
            ),
            "provenance": [{"rule_id": "ALICE-CONCURRENCY-001", "reviewer": "alice"}],
        }
        compiler_json = repo / "compiler.json"
        compiler_json.write_text(json.dumps(compiler_payload, indent=2), encoding="utf-8")

        prompt = (
            "Give second opinion on this change. Run the reviewer stage only. "
            "Read prompts/reviewer.prompt. Use compiler.json for compiled_prompt and diff at "
            f"{diff_path.name}. Write review.md and review.json in the repo root."
        )
        _codex_exec(codex_cmd, repo, codex_home, prompt, auth_key)

        review_md = repo / "review.md"
        review_json = repo / "review.json"
        self.assertTrue(review_md.is_file(), "review.md not created")
        self.assertTrue(review_json.is_file(), "review.json not created")
        with review_json.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertIn("findings", data, "review.json missing findings")
        self.assertIsInstance(data["findings"], list, "findings must be a list")
