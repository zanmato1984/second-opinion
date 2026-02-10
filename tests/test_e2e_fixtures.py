import json
import os
from pathlib import Path
import unittest

from tests.e2e_helpers import codex_exec, prepare_workspace


@unittest.skipUnless(
    os.environ.get("CODEX_E2E") == "1",
    "Set CODEX_E2E=1 to enable Codex end-to-end tests.",
)
class CodexE2EFixtureTest(unittest.TestCase):
    def _prepare_workspace(self):
        return prepare_workspace(self.addCleanup)

    def test_fixture_pipeline_sentinels(self):
        codex_cmd, codex_home, repo, _diff_path, auth_key = self._prepare_workspace()

        prompt = (
            "Use the test-second-opinion skill. "
            "Run the compiler and reviewer stages using tests/fixtures assets only. "
            "Write compiler.json, review.md, and review.json in the repo root. "
            "The diff is at fixture.diff."
        )
        fixture_diff = repo / "fixture.diff"
        fixture_source = Path(__file__).resolve().parent / "fixtures" / "patch.diff"
        fixture_diff.write_text(fixture_source.read_text(encoding="utf-8"), encoding="utf-8")
        codex_exec(codex_cmd, repo, codex_home, prompt, auth_key)

        compiler_json = repo / "compiler.json"
        self.assertTrue(compiler_json.is_file(), "compiler.json not created")
        with compiler_json.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertEqual(["evil"], data.get("selected_experts", []))
        self.assertEqual(["evil-process"], data.get("selected_processes", []))
        self.assertEqual(["evil"], data.get("selected_policies", []))
        self.assertNotIn("pr-baseline", data.get("selected_processes", []))
        self.assertNotIn("security", data.get("selected_policies", []))
        self.assertNotIn("compat", data.get("selected_policies", []))
        compiled_prompt = data.get("compiled_prompt", "")
        self.assertIn("TEST-EXPERT-SENTINEL", compiled_prompt)
        self.assertIn("TEST-POLICY-SENTINEL", compiled_prompt)
        self.assertIn("TEST-FRAGMENT-SENTINEL", compiled_prompt)
        rationale = data.get("selection_rationale", {})
        primary = rationale.get("primary_process") or {}
        self.assertEqual("evil-process", primary.get("process"))

        review_md = repo / "review.md"
        self.assertTrue(review_md.is_file(), "review.md not created")
        review_text = review_md.read_text(encoding="utf-8")
        self.assertIn("TEST-PROCESS-SENTINEL", review_text)
        review_json = repo / "review.json"
        self.assertTrue(review_json.is_file(), "review.json not created")
        review_data = json.loads(review_json.read_text(encoding="utf-8"))
        findings = review_data.get("findings", [])
        self.assertEqual(2, len(findings))
        by_source = {(f.get("source", {}).get("type"), f.get("source", {}).get("id")): f for f in findings}
        process_finding = by_source.get(("process", "evil-process"))
        self.assertIsNotNone(process_finding, "missing process finding")
        process_message = process_finding.get("message", "")
        self.assertIn("ignored lock order comment", process_message)

        expert_finding = by_source.get(("rule", "EVIL-PIPELINE-001"))
        self.assertIsNotNone(expert_finding, "missing expert finding")
        expert_message = expert_finding.get("message", "")
        self.assertIn("lock muB before muA", expert_message)
        self.assertIn("reverse lock order", expert_message)
