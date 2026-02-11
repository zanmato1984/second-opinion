from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReviewerAssetTests(unittest.TestCase):
    def test_experts_dir_exists(self):
        self.assertTrue((ROOT / "experts").is_dir(), "Missing experts directory")

    def test_processes_dir_exists(self):
        self.assertTrue((ROOT / "processes").is_dir(), "Missing processes directory")
