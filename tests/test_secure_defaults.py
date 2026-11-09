import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tests import e2e_helpers as helpers
from scripts.install_skill import install

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "processes" / "review-branch" / "prepare_review.sh"


class HarnessSecurityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / "codex"
        self.home.mkdir()

    def test_no_implicit_personal_auth_or_config(self):
        personal = self.root / "personal"
        (personal / ".codex").mkdir(parents=True)
        (personal / ".codex" / "auth.json").write_text('{"OPENAI_API_KEY":"personal"}')
        (personal / ".codex" / "config.toml").write_text('sandbox_mode="danger-full-access"')
        with patch.dict(os.environ, {"HOME": str(personal), "OPENAI_API_KEY": "ambient"}, clear=True):
            with self.assertRaisesRegex(AssertionError, "CODEX_E2E_API_KEY"):
                helpers._ensure_auth()
            helpers._write_config(self.home)
        self.assertFalse((self.home / "auth.json").exists())
        config = (self.home / "config.toml").read_text()
        self.assertNotIn("danger-full-access", config)
        self.assertIn('inherit = "core"', config)
        self.assertIn('include_only = ["HOME", "PATH", "TMPDIR", "LANG"]', config)
        self.assertIn('allow_login_shell = false', config)
        self.assertIn('shell_snapshot = false', config)

    def test_child_has_minimal_environment_and_no_unsandboxed_fallback(self):
        with patch.dict(os.environ, {"GH_TOKEN": "github-secret", "AWS_SECRET_ACCESS_KEY": "aws-secret",
                                     "OPENAI_API_KEY": "personal-secret", "CODEX_API_KEY": "ambient-codex-secret",
                                     "CODEX_E2E_API_KEY": "test-secret"}, clear=True):
            self.assertEqual(helpers._ensure_auth(), "test-secret")
            with patch.object(helpers.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "test-secret", "test-secret")) as run:
                with self.assertRaises(AssertionError) as error:
                    helpers.codex_exec("codex", self.root, self.home, "review", "test-secret")
        run.assert_called_once()
        argv = run.call_args.args[0]
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", argv)
        self.assertEqual(argv[argv.index("-s") + 1], "workspace-write")
        self.assertEqual(argv[argv.index("-a") + 1], "never")
        self.assertIn('shell_environment_policy.inherit="core"', argv)
        self.assertIn('shell_environment_policy.include_only=["HOME","PATH","TMPDIR","LANG"]', argv)
        self.assertIn("allow_login_shell=false", argv)
        self.assertEqual(argv[argv.index("--disable") + 1], "shell_snapshot")
        env = run.call_args.kwargs["env"]
        self.assertEqual(set(env), {"PATH", "HOME", "TMPDIR", "CODEX_HOME", "CODEX_API_KEY", "LANG"})
        self.assertEqual(env["CODEX_API_KEY"], "test-secret")
        self.assertEqual(env["HOME"], str(self.root / "home"))
        self.assertNotIn("test-secret", str(error.exception))

    def test_fixture_installation_is_explicit(self):
        helpers._install_skills(self.home)
        installed = self.home / "skills" / "second-opinion"
        self.assertTrue((installed / "prompts" / "reviewer.prompt").is_file())
        self.assertFalse((installed / "tests").exists())
        self.assertTrue((installed / "scripts" / "install_skill.py").is_file())
        self.assertTrue((installed / "docs" / "e2e-security.md").is_file())
        self.assertFalse(list(installed.rglob("__pycache__")))
        self.assertFalse((self.home / "skills" / "test-second-opinion").exists())
        fixture_home = self.root / "fixture-codex"
        helpers._install_skills(fixture_home, include_fixtures=True)
        self.assertTrue((fixture_home / "skills" / "second-opinion" / "tests" / "fixtures" / "patch.diff").is_file())
        self.assertTrue((fixture_home / "skills" / "test-second-opinion" / "SKILL.md").is_file())

    def test_production_export_refuses_existing_or_symlinked_installation(self):
        existing = self.root / "existing"
        existing.mkdir()
        (existing / "unique.txt").write_text("keep me")
        symlink = self.root / "link"
        symlink.symlink_to(existing, target_is_directory=True)
        for destination in (existing, symlink):
            with self.assertRaises(FileExistsError):
                install(ROOT, destination)
        self.assertEqual((existing / "unique.txt").read_text(), "keep me")


class ReviewPreparationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.com",
                    "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.com"}
        self.git(self.source, "init", "-b", "main")
        (self.source / "base.txt").write_text("base\n")
        self.git(self.source, "add", ".")
        self.git(self.source, "commit", "-m", "base")
        self.git(self.source, "checkout", "-b", "feature")
        (self.source / "feature.txt").write_text("feature\n")
        self.git(self.source, "add", ".")
        self.git(self.source, "commit", "-m", "feature")
        self.feature_sha = self.git(self.source, "rev-parse", "HEAD").stdout.strip()
        self.git(self.source, "checkout", "main")
        (self.source / "upstream.txt").write_text("new base\n")
        self.git(self.source, "add", ".")
        self.git(self.source, "commit", "-m", "advance base")
        self.repo = self.root / "repo"
        self.git(self.root, "clone", str(self.source), str(self.repo))
        self.git(self.repo, "remote", "add", "upstream", str(self.source))
        self.worktree = self.repo / ".codex" / "worktrees" / "review-feature"

    def git(self, cwd, *args):
        return subprocess.run(["git", *args], cwd=cwd, env=self.env, text=True,
                              capture_output=True, check=True)

    def prepare(self, *extra):
        return self.prepare_url(str(self.source), *extra)

    def prepare_url(self, url, *extra):
        return subprocess.run(["bash", str(SCRIPT), url, "feature", "--base", "main", *extra],
                              cwd=self.repo, env=self.env, text=True, capture_output=True)

    def assert_rejected_before_fetch(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ERROR:", result.stdout)
        self.assertNotIn("Fetching", result.stdout)
        self.assertFalse((self.repo / ".git" / "FETCH_HEAD").exists())
        self.assertFalse(self.worktree.exists())

    def test_default_preserves_review_head(self):
        result = self.prepare()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git(self.worktree, "rev-parse", "HEAD").stdout.strip(), self.feature_sha)
        self.assertFalse((self.worktree / "upstream.txt").exists())

    def test_merge_requires_explicit_opt_in(self):
        result = self.prepare("--merge-base")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.worktree / "upstream.txt").exists())
        parents = self.git(self.worktree, "rev-list", "--parents", "-n", "1", "HEAD").stdout.split()
        self.assertEqual(len(parents), 3)

    def test_existing_dirty_worktree_is_preserved(self):
        self.assertEqual(self.prepare().returncode, 0)
        unique = self.worktree / "unique-uncommitted.txt"
        unique.write_text("keep me")
        result = self.prepare()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists", result.stdout)
        self.assertEqual(unique.read_text(), "keep me")
        self.assertEqual(self.git(self.worktree, "rev-parse", "HEAD").stdout.strip(), self.feature_sha)

    def test_existing_untracked_path_is_preserved(self):
        self.worktree.mkdir(parents=True)
        (self.worktree / "unique.txt").write_text("keep me")
        self.assertNotEqual(self.prepare().returncode, 0)
        self.assertEqual((self.worktree / "unique.txt").read_text(), "keep me")

    def test_plaintext_and_lookalike_pr_urls_are_rejected(self):
        for url in ("http://github.com/owner/repo/pull/1", "git://example.com/repo", "https://github.com.evil/owner/repo/pull/1"):
            with self.subTest(url=url):
                result = subprocess.run(["bash", str(SCRIPT), url], cwd=self.repo, env=self.env,
                                        text=True, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("ERROR:", result.stdout)
        self.assertFalse(self.worktree.exists())

    def test_helper_and_option_forms_are_rejected_without_side_effects(self):
        for url in ("http::http://127.0.0.1:9/repo", "https::http://127.0.0.1:9/repo",
                    "ext::unexpected", "file:///tmp/repo", "--upload-pack=unexpected",
                    "http://127.0.0.1:9/repo", "git://127.0.0.1:9/repo"):
            with self.subTest(url=url):
                self.assert_rejected_before_fetch(self.prepare_url(url))
        self.assertNotIn("codex_review_remote", self.git(self.repo, "remote").stdout)

    def test_upstream_plaintext_and_helper_urls_are_rejected_before_fetch(self):
        for url in ("http://127.0.0.1:9/repo", "git://127.0.0.1:9/repo",
                    "http::http://127.0.0.1:9/repo"):
            with self.subTest(url=url):
                self.git(self.repo, "remote", "set-url", "upstream", url)
                self.assert_rejected_before_fetch(self.prepare())

    def test_review_and_upstream_rewrite_downgrades_are_rejected_before_fetch(self):
        secure_url = "https://review.invalid/repo"
        self.git(self.repo, "config", "url.http://127.0.0.1:9/repo.insteadOf", secure_url)
        self.assert_rejected_before_fetch(self.prepare_url(secure_url))
        self.git(self.repo, "remote", "set-url", "upstream", secure_url)
        self.assert_rejected_before_fetch(self.prepare())

    def test_existing_review_remote_rewrite_downgrade_is_rejected_before_fetch(self):
        self.git(self.repo, "remote", "add", "codex_review_remote", "https://review.invalid/repo")
        self.git(self.repo, "config", "url.http::http://127.0.0.1:9/repo.insteadOf", "https://review.invalid/repo")
        self.assert_rejected_before_fetch(self.prepare())

    def test_https_url_with_secure_local_rewrite_succeeds(self):
        secure_url = "https://review.invalid/repo"
        self.git(self.repo, "config", f"url.{self.source}.insteadOf", secure_url)
        self.git(self.repo, "remote", "set-url", "upstream", secure_url)
        result = self.prepare_url(secure_url)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git(self.worktree, "rev-parse", "HEAD").stdout.strip(), self.feature_sha)

    def test_existing_local_directory_with_spaces_succeeds(self):
        source = self.root / "source with spaces"
        self.source.rename(source)
        self.git(self.repo, "remote", "set-url", "upstream", str(source))
        result = self.prepare_url(str(source))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git(self.worktree, "rev-parse", "HEAD").stdout.strip(), self.feature_sha)

    def test_ssh_url_and_scp_style_use_allowed_transport(self):
        # Real Git's SSH transport with a local upload-pack, never a network call.
        ssh = self.root / "ssh-stub"
        ssh.write_text('#!/bin/sh\nexec git-upload-pack "$LOCAL_SOURCE"\n')
        ssh.chmod(0o755)
        self.env.update({"GIT_SSH_COMMAND": str(ssh), "GIT_SSH_VARIANT": "ssh",
                         "LOCAL_SOURCE": str(self.source)})
        self.git(self.repo, "remote", "set-url", "upstream", "git@review.invalid:repo")
        result = self.prepare_url("ssh://git@review.invalid/repo")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git(self.worktree, "rev-parse", "HEAD").stdout.strip(), self.feature_sha)

    def test_actual_git_protocol_allowlist_overrides_ambient_config(self):
        # remote.<name>.vcs overrides URL-based helper selection in Git. A URL
        # preflight alone cannot enforce the transport used for this remote.
        self.git(self.repo, "config", "remote.upstream.vcs", "http")
        self.git(self.repo, "config", "protocol.http.allow", "always")
        self.env["GIT_ALLOW_PROTOCOL"] = "http"
        result = self.prepare()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("transport 'http' not allowed", result.stderr)
        self.assertFalse(self.worktree.exists())

    def test_option_like_branch_is_rejected_before_fetch(self):
        result = subprocess.run(["bash", str(SCRIPT), str(self.source), "--upload-pack=unexpected", "--base", "main"],
                                cwd=self.repo, env=self.env, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unsupported option", result.stdout)
        self.assertNotIn("Fetching", result.stdout)

    def test_missing_or_extra_arguments_are_rejected_before_fetch(self):
        for args in ((str(self.source), "feature", "extra"),
                     (str(self.source), "feature", "--base"),
                     (str(self.source), "feature", "--paths")):
            with self.subTest(args=args):
                result = subprocess.run(["bash", str(SCRIPT), *args], cwd=self.repo,
                                        env=self.env, text=True, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("Fetching", result.stdout)
