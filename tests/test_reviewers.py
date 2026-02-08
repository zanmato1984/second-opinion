from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REVIEWERS = {
    "alice": {
        "dir": ROOT / "reviewers" / "alice",
        "criteria": "criteria.md",
        "meta": "meta.yaml",
        "meta_markers": ["id: alice", "kind: person"],
    },
    "re2": {
        "dir": ROOT / "reviewers" / "re2",
        "criteria": "criteria.md",
        "meta": "meta.yaml",
        "meta_markers": ["id: re2", "kind: process"],
    },
}


class ReviewerTests(unittest.TestCase):
    def test_reviewer_dirs_exist(self):
        for name, info in REVIEWERS.items():
            self.assertTrue(info["dir"].is_dir(), f"Missing reviewer directory: {name}")

    def test_reviewer_files_exist(self):
        for name, info in REVIEWERS.items():
            criteria = info["dir"] / info["criteria"]
            meta = info["dir"] / info["meta"]
            self.assertTrue(criteria.is_file(), f"Missing criteria for reviewer: {name}")
            self.assertTrue(meta.is_file(), f"Missing meta for reviewer: {name}")

    def test_meta_contains_markers(self):
        for name, info in REVIEWERS.items():
            meta = (info["dir"] / info["meta"]).read_text(encoding="utf-8")
            for marker in info["meta_markers"]:
                self.assertIn(marker, meta, f"Reviewer {name} meta missing: {marker}")

