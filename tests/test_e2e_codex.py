import json
import os
import unittest

from tests.e2e_helpers import codex_exec, prepare_workspace


@unittest.skipUnless(
    os.environ.get("CODEX_E2E") == "1",
    "Set CODEX_E2E=1 to enable Codex end-to-end tests.",
)
class CodexE2ETest(unittest.TestCase):
    def _prepare_workspace(self):
        return prepare_workspace(self.addCleanup)

    def test_codex_runs_second_opinion_skill(self):
        codex_cmd, codex_home, repo, _diff_path, auth_key = self._prepare_workspace()

        prompt = (
            "Give second opinion on this change. "
            "Run the Second Opinion review workflow and write review.md and review.json in the repo root."
        )
        codex_exec(codex_cmd, repo, codex_home, prompt, auth_key)

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
        codex_exec(codex_cmd, repo, codex_home, prompt, auth_key)

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
                {"tag": "component:tidb/ddl", "why": "sample component"},
                {"tag": "risk:concurrency", "why": "sample risk"},
            ],
        }
        tagger_json = repo / "tagger.json"
        tagger_json.write_text(json.dumps(tagger_payload, indent=2), encoding="utf-8")

        prompt = (
            "Give second opinion on this change. Run the compiler stage only. "
            "Read prompts/compiler.prompt. Use tagger.json for derived tags, experts/* for rule metadata and "
            "criteria, processes/* for workflow metadata and criteria, and write compiler.json in the repo root. "
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

    def test_codex_reviewer_stage(self):
        codex_cmd, codex_home, repo, diff_path, auth_key = self._prepare_workspace()

        compiler_payload = {
            "selected_experts": ["example-expert"],
            "rules_used": {"example-expert": ["EXAMPLE-RULE-001"]},
            "selected_processes": [],
            "selected_policies": ["example-policy"],
            "selection_rationale": {
                "user_override": None,
                "candidates": [],
                "primary_process": None,
                "secondary_processes": [],
                "tie_breakers": ["specificity", "cost"],
                "budget": "medium",
            },
            "compiled_prompt": (
                "You are the review stage. Use the diff to produce review.md and review.json. "
                "review.json must include a findings array."
            ),
            "provenance": [{"rule_id": "EXAMPLE-RULE-001", "expert": "example-expert"}],
        }
        compiler_json = repo / "compiler.json"
        compiler_json.write_text(json.dumps(compiler_payload, indent=2), encoding="utf-8")

        prompt = (
            "Give second opinion on this change. Run the reviewer stage only. "
            "Read prompts/reviewer.prompt. Use compiler.json for compiled_prompt and diff at "
            f"{diff_path.name}. Write review.md and review.json in the repo root."
        )
        codex_exec(codex_cmd, repo, codex_home, prompt, auth_key)

        review_md = repo / "review.md"
        review_json = repo / "review.json"
        self.assertTrue(review_md.is_file(), "review.md not created")
        self.assertTrue(review_json.is_file(), "review.json not created")
        with review_json.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertIn("findings", data, "review.json missing findings")
        self.assertIsInstance(data["findings"], list, "findings must be a list")
