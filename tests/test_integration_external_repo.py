import json
import os
from pathlib import Path
import subprocess
import unittest

from tests.e2e_helpers import codex_exec, prepare_workspace


def _run(cmd, cwd):
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


@unittest.skipUnless(
    os.environ.get("CODEX_E2E") == "1",
    "Set CODEX_E2E=1 to enable Codex end-to-end tests.",
)
class CodexIntegrationExternalRepoTest(unittest.TestCase):
    def _prepare_workspace(self):
        return prepare_workspace(self.addCleanup)

    def test_external_repo_diff_compiler(self):
        repo_path = os.environ.get("SO_INTEGRATION_REPO")
        ref = os.environ.get("SO_INTEGRATION_REF")
        if not repo_path or not ref:
            raise unittest.SkipTest(
                "Set SO_INTEGRATION_REPO and SO_INTEGRATION_REF to enable external repo integration test."
            )

        repo_dir = Path(repo_path)
        if not repo_dir.is_dir():
            raise unittest.SkipTest(f"SO_INTEGRATION_REPO is not a directory: {repo_dir}")

        git_dir = repo_dir / ".git"
        if not git_dir.exists():
            raise unittest.SkipTest(f"SO_INTEGRATION_REPO is not a git repo: {repo_dir}")

        diff = _run(["git", "show", ref], cwd=repo_dir).stdout
        if not diff.strip():
            raise AssertionError("external repo diff is empty")

        codex_cmd, codex_home, workspace, _diff_path, auth_key = self._prepare_workspace()
        diff_path = workspace / "external.diff"
        diff_path.write_text(diff, encoding="utf-8")

        prompt = (
            "Give second opinion on this change. Run the compiler stage only. "
            "Read prompts/compiler.prompt. Use the diff at external.diff. Use experts/*, processes/*, "
            "policies/*, and fragments/* for metadata and criteria. Write compiler.json in the repo root."
        )
        codex_exec(codex_cmd, workspace, codex_home, prompt, auth_key)

        compiler_json = workspace / "compiler.json"
        self.assertTrue(compiler_json.is_file(), "compiler.json not created")
        with compiler_json.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        for field in [
            "selected_experts",
            "rules_used",
            "selected_processes",
            "selected_policies",
            "selection_rationale",
            "compiled_prompt",
            "provenance",
        ]:
            self.assertIn(field, data, f"compiler.json missing {field}")
