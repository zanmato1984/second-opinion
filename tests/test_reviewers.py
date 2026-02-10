from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPERTS = {
    "alice": {
        "dir": ROOT / "experts" / "alice",
        "criteria": "criteria.md",
        "meta": "meta.yaml",
        "meta_markers": ["id: alice", "kind: person"],
    },
}
PROCESSES = {
    "re2": {
        "dir": ROOT / "processes" / "re2",
        "criteria": "criteria.md",
        "meta": "meta.yaml",
        "meta_markers": [
            "id: re2",
            "kind: process",
            "priority:",
            "cost:",
            "mode:",
            "default:",
            "output_contract:",
            "activation:",
        ],
    },
    "pr-baseline": {
        "dir": ROOT / "processes" / "pr-baseline",
        "criteria": "criteria.md",
        "meta": "meta.yaml",
        "meta_markers": [
            "id: pr-baseline",
            "kind: process",
            "priority:",
            "cost:",
            "mode:",
            "default:",
            "output_contract:",
            "activation:",
        ],
    },
}


class ExpertTests(unittest.TestCase):
    def test_expert_dirs_exist(self):
        for name, info in EXPERTS.items():
            self.assertTrue(info["dir"].is_dir(), f"Missing expert directory: {name}")

    def test_expert_files_exist(self):
        for name, info in EXPERTS.items():
            criteria = info["dir"] / info["criteria"]
            meta = info["dir"] / info["meta"]
            self.assertTrue(criteria.is_file(), f"Missing criteria for expert: {name}")
            self.assertTrue(meta.is_file(), f"Missing meta for expert: {name}")

    def test_meta_contains_markers(self):
        for name, info in EXPERTS.items():
            meta = (info["dir"] / info["meta"]).read_text(encoding="utf-8")
            for marker in info["meta_markers"]:
                self.assertIn(marker, meta, f"Expert {name} meta missing: {marker}")


class ProcessTests(unittest.TestCase):
    def test_process_dirs_exist(self):
        for name, info in PROCESSES.items():
            self.assertTrue(info["dir"].is_dir(), f"Missing process directory: {name}")

    def test_process_files_exist(self):
        for name, info in PROCESSES.items():
            criteria = info["dir"] / info["criteria"]
            meta = info["dir"] / info["meta"]
            self.assertTrue(criteria.is_file(), f"Missing criteria for process: {name}")
            self.assertTrue(meta.is_file(), f"Missing meta for process: {name}")

    def test_process_meta_contains_markers(self):
        for name, info in PROCESSES.items():
            meta = (info["dir"] / info["meta"]).read_text(encoding="utf-8")
            for marker in info["meta_markers"]:
                self.assertIn(marker, meta, f"Process {name} meta missing: {marker}")
