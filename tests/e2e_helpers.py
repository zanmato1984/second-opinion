import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from scripts.install_skill import install

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(cmd, cwd, env=None):
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _require_tool(name):
    if shutil.which(name) is None:
        raise unittest.SkipTest(f"Required tool not found: {name}")


def _ensure_auth():
    key = os.environ.get("CODEX_E2E_API_KEY")
    if not key:
        raise AssertionError("Set CODEX_E2E_API_KEY to a dedicated test API key.")
    return key


def _write_config(codex_home):
    codex_home.mkdir(parents=True, exist_ok=True)
    (codex_home / "config.toml").write_text(
        'approval_policy = "never"\n'
        'sandbox_mode = "workspace-write"\n'
        '[sandbox_workspace_write]\nnetwork_access = false\n'
        '[shell_environment_policy]\ninherit = "none"\n',
        encoding="utf-8",
    )


def _install_skills(codex_home, *, include_fixtures=False):
    skill_dst = codex_home / "skills" / "second-opinion"
    install(REPO_ROOT, skill_dst, include_fixtures=include_fixtures)

    skills_src = REPO_ROOT / "skills"
    if skills_src.is_dir():
        for child in skills_src.iterdir():
            if child.name == "test-second-opinion" and not include_fixtures:
                continue
            if not child.is_dir():
                continue
            if not (child / "SKILL.md").is_file():
                continue
            dst = codex_home / "skills" / child.name
            shutil.copytree(
                child,
                dst,
                ignore=shutil.ignore_patterns(".git", "__pycache__"),
            )


def codex_exec(codex_cmd, repo, codex_home, prompt, auth_key):
    cmd = [
        codex_cmd,
        "-C",
        str(repo),
        "-s",
        "workspace-write",
        "-a",
        "never",
        "-c",
        "sandbox_workspace_write.network_access=false",
        "-c",
        'shell_environment_policy.inherit="none"',
    ]
    model = os.environ.get("CODEX_E2E_MODEL")
    if model:
        cmd.extend(["-m", model])
    cmd.extend(["exec", prompt])

    isolated_home = codex_home.parent / "home"
    isolated_tmp = codex_home.parent / "tmp"
    isolated_home.mkdir(exist_ok=True)
    isolated_tmp.mkdir(exist_ok=True)
    env = {
        "PATH": os.defpath,
        "HOME": str(isolated_home),
        "TMPDIR": str(isolated_tmp),
        "CODEX_HOME": str(codex_home),
        "OPENAI_API_KEY": auth_key,
        "LANG": "en_US.UTF-8",
    }
    timeout = int(os.environ.get("CODEX_E2E_TIMEOUT", "600"))
    result = subprocess.run(
        cmd,
        cwd=repo,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"codex exec failed (exit {result.returncode}); child output withheld to protect credentials"
        )


def prepare_workspace(add_cleanup, *, include_fixtures=False):
    codex_cmd = shutil.which(os.environ.get("CODEX_E2E_CMD", "codex"))
    if codex_cmd is None:
        raise unittest.SkipTest("Required tool not found: codex")
    _require_tool(codex_cmd)
    _require_tool("git")

    tmp = tempfile.TemporaryDirectory()
    add_cleanup(tmp.cleanup)
    tmp_path = Path(tmp.name)

    codex_home = tmp_path / "codex_home"
    auth_key = _ensure_auth()
    _write_config(codex_home)
    _install_skills(codex_home, include_fixtures=include_fixtures)

    repo = tmp_path / "workspace"
    repo.mkdir()
    _run(["git", "init"], cwd=repo)
    _run(["git", "config", "user.email", "codex@example.com"], cwd=repo)
    _run(["git", "config", "user.name", "Codex"], cwd=repo)

    sample_file = repo / "main.go"
    sample_file.write_text(
        "package main\n\nfunc add(a, b int) int { return a + b }\n",
        encoding="utf-8",
    )
    _run(["git", "add", "main.go"], cwd=repo)
    _run(["git", "commit", "-m", "init"], cwd=repo)

    sample_file.write_text(
        "package main\n\nfunc add(a, b int) int { return a + b }\n\nfunc sub(a, b int) int { return a - b }\n",
        encoding="utf-8",
    )

    diff = _run(["git", "diff"], cwd=repo).stdout
    if not diff.strip():
        raise AssertionError("git diff returned empty output")
    diff_path = repo / "change.diff"
    diff_path.write_text(diff, encoding="utf-8")

    return codex_cmd, codex_home, repo, diff_path, auth_key
