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
        ],
    },
    "reviewer": {
        "path": ROOT / "prompts" / "reviewer.prompt",
        "required": ["review.md", "review.json", "compiled_prompt", "source"],
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
