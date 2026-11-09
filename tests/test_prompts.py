from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

PROMPTS = {
    "tagger": {
        "path": ROOT / "prompts" / "tagger.prompt",
        "required": ["Output JSON only", "signals", "tags"],
    },
    "compiler": {
        "path": ROOT / "prompts" / "compiler.prompt",
        "required": [
            "Output JSON only",
            "compiled_prompt",
            "provenance",
            "selection_rationale",
            "tests/fixtures",
            "persist this JSON as `second_opinion_meta.json`",
            "fragments/github-comment-contract.md",
        ],
    },
    "reviewer": {
        "path": ROOT / "prompts" / "reviewer.prompt",
        "required": [
            "second_opinion.md",
            "second_opinion.json",
            "second_opinion_github_comments.json",
            "compiled_prompt",
            "source",
            "Do not only print findings in chat",
            "Write required output files to the repository root on disk",
            "Source: <type>/<id> | [Second Opinion](https://github.com/PingCAP-QE/second-opinion)",
            "This stage is artifact-only",
            "Use review_context.language",
            "A draft never authorizes sending it",
            "prefer inline then file then general mode",
            "Do not emit an extra review body comment per finding",
            "subject_type=file",
            "consent belong exclusively to the parent",
        ],
    },
}


class PromptTests(unittest.TestCase):
    def test_prompt_files_exist(self):
        for name, info in PROMPTS.items():
            self.assertTrue(info["path"].is_file(), f"Missing {name} prompt: {info['path']}")

    def test_prompt_contains_required_markers(self):
        for name, info in PROMPTS.items():
            content = info["path"].read_text(encoding="utf-8")
            for marker in info["required"]:
                self.assertIn(marker, content, f"{name} prompt missing marker: {marker}")
