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
