import json
import os
import unittest

from tests.e2e_helpers import codex_exec, prepare_workspace


@unittest.skipUnless(
    os.environ.get("CODEX_E2E") == "1",
    "Set CODEX_E2E=1 to enable Codex end-to-end tests.",
)
class CodexIntegrationAssetsTest(unittest.TestCase):
    def _prepare_workspace(self):
        return prepare_workspace(self.addCleanup)

    def test_real_assets_compiler_selection(self):
        codex_cmd, codex_home, repo, diff_path, auth_key = self._prepare_workspace()

        tagger_payload = {
            "signals": [{"evidence": "main.go", "reason": "sample change"}],
            "tags": [
                {"tag": "lang:go", "why": "Go source"},
                {"tag": "component:ddl", "why": "sample component"},
                {"tag": "theme:testing", "why": "sample theme"},
            ],
        }
        tagger_json = repo / "tagger.json"
        tagger_json.write_text(json.dumps(tagger_payload, indent=2), encoding="utf-8")

        prompt = (
            "Give second opinion on this change. Run the compiler stage only. "
            "Read prompts/compiler.prompt. Use tagger.json for derived tags, experts/* for rule metadata and "
            "criteria, processes/* for workflow metadata and criteria, policies/* for policies, and fragments/* "
            "for shared fragments. Ensure selection_rationale is populated even when no assets match. "
            "Write compiler.json in the repo root. "
            f"The diff is at {diff_path.name}."
        )
        codex_exec(codex_cmd, repo, codex_home, prompt, auth_key)

        compiler_json = repo / "compiler.json"
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
