from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FRAGMENTS = [
    "evidence.md",
    "checklists.md",
    "output-cn.md",
    "output-en.md",
    "risk-matrix.md",
]
POLICIES = [
    "security.yaml",
    "compat.yaml",
]
FIXTURE_SENTINELS = {
    "experts/evil/criteria.md": ["TEST-EXPERT-SENTINEL", "lock muB before muA"],
    "processes/evil/criteria.md": [
        "TEST-PROCESS-SENTINEL",
        "ignored lock order comment",
    ],
    "policies/evil.yaml": ["TEST-POLICY-SENTINEL"],
    "fragments/evil.md": ["TEST-FRAGMENT-SENTINEL"],
}


class AssetTests(unittest.TestCase):
    def test_fragments_exist(self):
        fragments_dir = ROOT / "fragments"
        self.assertTrue(fragments_dir.is_dir(), "Missing fragments directory")
        for name in FRAGMENTS:
            self.assertTrue((fragments_dir / name).is_file(), f"Missing fragment: {name}")

    def test_policies_exist(self):
        policies_dir = ROOT / "policies"
        self.assertTrue(policies_dir.is_dir(), "Missing policies directory")
        for name in POLICIES:
            self.assertTrue((policies_dir / name).is_file(), f"Missing policy: {name}")

    def test_fixture_assets_exist(self):
        fixture_root = ROOT / "tests" / "fixtures"
        self.assertTrue(fixture_root.is_dir(), "Missing tests/fixtures directory")
        for rel_path in FIXTURE_SENTINELS:
            self.assertTrue(
                (fixture_root / rel_path).is_file(),
                f"Missing fixture asset: {rel_path}",
            )

    def test_fixture_sentinels(self):
        fixture_root = ROOT / "tests" / "fixtures"
        for rel_path, sentinels in FIXTURE_SENTINELS.items():
            content = (fixture_root / rel_path).read_text(encoding="utf-8")
            for sentinel in sentinels:
                self.assertIn(sentinel, content, f"Missing sentinel {sentinel} in {rel_path}")
