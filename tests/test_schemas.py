import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

SCHEMAS = {
    "review_context": {
        "path": ROOT / "schemas" / "review-context.schema.json",
        "required": ["language", "focus", "budget", "process_override", "draft_github_comments"],
    },
    "selection": {
        "path": ROOT / "schemas" / "selection.schema.json",
        "required": ["signals", "tags"],
    },
    "compile": {
        "path": ROOT / "schemas" / "compile.schema.json",
        "required": [
            "selected_experts",
            "rules_used",
            "selected_processes",
            "selected_policies",
            "selection_rationale",
            "compiled_prompt",
            "provenance",
        ],
    },
    "review": {
        "path": ROOT / "schemas" / "review.schema.json",
        "required": ["findings"],
    },
    "github_comments": {
        "path": ROOT / "schemas" / "second-opinion-github-comments.schema.json",
        "required": ["repo_url", "comments"],
    },
}


class SchemaTests(unittest.TestCase):
    def _load(self, path: Path):
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_schema_files_exist(self):
        for name, info in SCHEMAS.items():
            self.assertTrue(info["path"].is_file(), f"Missing {name} schema: {info['path']}")

    def test_schema_structure(self):
        for name, info in SCHEMAS.items():
            data = self._load(info["path"])
            self.assertEqual(data.get("type"), "object", f"{name} schema must be an object")
            required = data.get("required", [])
            for field in info["required"]:
                self.assertIn(field, required, f"{name} schema missing required field: {field}")
            self.assertFalse(
                data.get("additionalProperties", True),
                f"{name} schema should set additionalProperties false",
            )

    def test_github_comments_item_contract(self):
        data = self._load(ROOT / "schemas" / "second-opinion-github-comments.schema.json")
        self.assertEqual(
            data["properties"]["repo_url"].get("const"),
            "https://github.com/PingCAP-QE/second-opinion",
            "github_comments repo_url must point to the Second Opinion repository",
        )
        item = data["properties"]["comments"]["items"]
        required = item.get("required", [])
        for field in ["mode", "body", "source", "severity", "attribution_line"]:
            self.assertIn(field, required, f"github_comments item missing required field: {field}")
        self.assertEqual(
            set(item["properties"]["mode"]["enum"]),
            {"inline", "file", "general"},
            "github_comments mode enum must include inline, file, and general",
        )
        self.assertIn(
            "Second Opinion",
            item["properties"]["attribution_line"]["pattern"],
            "github_comments attribution line must include markdown link label",
        )
