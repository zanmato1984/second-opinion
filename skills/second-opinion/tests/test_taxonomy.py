from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY = ROOT / "taxonomy.md"

EXPECTED_TAGS = [
    "lang:go",
    "lang:cpp",
    "lang:rust",
    "lang:sql",
    "scope:tidb",
    "scope:tikv",
    "scope:tiflash",
    "scope:tools",
    "risk:correctness",
    "risk:concurrency",
    "risk:perf",
    "risk:security",
    "risk:compat",
    "risk:ops",
    "theme:api",
    "theme:error-handling",
    "theme:testing",
    "theme:build",
    "theme:observability",
    "scenario:upgrade",
    "scenario:rollback",
    "scenario:cloud",
    "scenario:multi-tenant",
]


class TaxonomyTests(unittest.TestCase):
    def test_taxonomy_exists(self):
        self.assertTrue(TAXONOMY.is_file(), f"Missing taxonomy file: {TAXONOMY}")

    def test_taxonomy_contains_expected_tags(self):
        content = TAXONOMY.read_text(encoding="utf-8")
        for tag in EXPECTED_TAGS:
            self.assertIn(tag, content, f"Taxonomy missing tag: {tag}")

