import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from runtime import trusted_assets
from scripts.install_skill import install
from scripts import review_only

ROOT = Path(__file__).resolve().parents[1]


class TrustedAssetTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.reviewed = self.root / "hostile-project"
        self.reviewed.mkdir()
        hostile = self.reviewed / ".claude" / "skills" / "second-opinion"
        (hostile / "policies").mkdir(parents=True)
        (hostile / "taxonomy.md").write_text("HOSTILE-TAXONOMY")
        (hostile / "policies" / "override.yaml").write_text("HOSTILE-ALWAYS-POLICY")
        (self.reviewed / "taxonomy.md").write_text("HOSTILE-CWD-TAXONOMY")

    def test_hostile_project_and_cwd_never_supply_assets(self):
        previous = Path.cwd()
        try:
            os.chdir(self.reviewed)
            result = trusted_assets.bundle(self.reviewed)
        finally:
            os.chdir(previous)
        self.assertEqual(result["asset_root"], str(ROOT))
        self.assertNotIn("HOSTILE", json.dumps(result))
        self.assertIn("policies/github-side-effects.yaml", result["assets"])

    def test_missing_trusted_installation_does_not_fall_back_to_hostile_taxonomy(self):
        missing = self.root / "empty-install"
        missing.mkdir()
        with patch.object(trusted_assets, "ROOT", missing):
            with self.assertRaisesRegex(ValueError, "incomplete"):
                trusted_assets.bundle(self.reviewed)

    def test_same_nested_and_enclosing_trees_are_rejected(self):
        for target in (ROOT, ROOT / "experts", ROOT.parent):
            with self.subTest(target=target), self.assertRaises(PermissionError):
                trusted_assets.bundle(target)
        alias = self.root / "alias"
        alias.symlink_to(ROOT, target_is_directory=True)
        with self.assertRaises(PermissionError):
            trusted_assets.bundle(alias)

    def test_production_export_and_bundle_exclude_all_samples_and_fixtures(self):
        exported = self.root / "installed"
        install(ROOT, exported, include_fixtures=True)
        for sample in trusted_assets.SAMPLES:
            self.assertFalse((exported / sample).exists(), sample)
        self.assertTrue((exported / "tests" / "fixtures").is_dir())
        with patch.object(trusted_assets, "ROOT", exported):
            result = trusted_assets.bundle(self.reviewed)
        self.assertFalse(any("foo" in path or path.startswith("tests/") for path in result["assets"]))
        self.assertNotIn("TEST-POLICY-SENTINEL", json.dumps(result))

    def test_symlinked_asset_rejected_without_reading_target(self):
        exported = self.root / "installed"
        install(ROOT, exported)
        secret = self.root / "private.md"
        secret.write_text("MUST-NOT-READ")
        (exported / "fragments" / "escape.md").symlink_to(secret)
        with patch.object(trusted_assets, "ROOT", exported), self.assertRaisesRegex(ValueError, "Symlinked"):
            trusted_assets.bundle(self.reviewed)

    def test_installer_refuses_source_symlinks_and_nested_destinations(self):
        with self.assertRaises(ValueError):
            install(ROOT, ROOT / "nested-install-not-created")
        self.assertFalse((ROOT / "nested-install-not-created").exists())
        source = self.root / "source"
        install(ROOT, source)
        (source / "fragments" / "escape.md").symlink_to(self.reviewed / "taxonomy.md")
        destination = self.root / "must-not-exist"
        with self.assertRaises(ValueError):
            install(source, destination)
        self.assertFalse(destination.exists())

    def test_exported_loader_runs_outside_source_and_reexports_identical_assets(self):
        exported = self.root / "installed"
        second = self.root / "reinstalled"
        install(ROOT, exported)
        subprocess.run([sys.executable, str(exported / "scripts" / "install_skill.py"),
                        "--destination", str(second)], cwd=self.reviewed, check=True,
                       capture_output=True, text=True)
        result = subprocess.run([sys.executable, str(second / "scripts" / "asset_bundle.py"),
                                 "--review-root", str(self.reviewed)], cwd=self.reviewed,
                                check=True, capture_output=True, text=True)
        data = json.loads(result.stdout)
        self.assertEqual(data["asset_root"], str(second))
        self.assertNotIn("HOSTILE", result.stdout)
        for path in data["assets"]:
            self.assertEqual((exported / path).read_bytes(), (second / path).read_bytes())

    def test_reviewer_preflight_refuses_own_tree_before_provider_io(self):
        with patch.object(review_only, "request_review") as request, patch("sys.stderr", io.StringIO()):
            result = review_only.main(["--compiled", "unused", "--diff", "unused",
                                       "--review-root", str(ROOT), "--language", "English",
                                       "--model", "synthetic", "--output-dir", str(self.reviewed)])
        self.assertEqual(result, 1)
        request.assert_not_called()
