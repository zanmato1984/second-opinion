import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

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


def _ensure_auth(codex_home):
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"]
    auth_src = Path(
        os.environ.get(
            "CODEX_E2E_AUTH_SOURCE",
            Path.home() / ".codex" / "auth.json",
        )
    )
    if auth_src.is_file():
        codex_home.mkdir(parents=True, exist_ok=True)
        dst = codex_home / "auth.json"
        shutil.copy2(auth_src, dst)
        try:
            payload = json.loads(auth_src.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AssertionError(f"Invalid auth.json: {auth_src}") from exc
        key = payload.get("OPENAI_API_KEY")
        if not key:
            raise AssertionError(f"auth.json missing OPENAI_API_KEY: {auth_src}")
        return key
    raise AssertionError(
        "Codex auth not found. Run `codex login`, set OPENAI_API_KEY, or set "
        "CODEX_E2E_AUTH_SOURCE to a valid auth.json."
    )


def _copy_config(codex_home):
    config_src = Path(
        os.environ.get(
            "CODEX_E2E_CONFIG_SOURCE",
            Path.home() / ".codex" / "config.toml",
        )
    )
    if config_src.is_file():
        codex_home.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config_src, codex_home / "config.toml")


def _install_skills(codex_home):
    skill_dst = codex_home / "skills" / "second-opinion"
    skill_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        REPO_ROOT,
        skill_dst,
        ignore=shutil.ignore_patterns(".git", "__pycache__"),
    )

    skills_src = REPO_ROOT / "skills"
    if skills_src.is_dir():
        for child in skills_src.iterdir():
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
        "--dangerously-bypass-approvals-and-sandbox",
    ]
    model = os.environ.get("CODEX_E2E_MODEL")
    if model:
        cmd.extend(["-m", model])
    cmd.extend(["exec", prompt])

    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    if auth_key and not env.get("OPENAI_API_KEY"):
        env["OPENAI_API_KEY"] = auth_key
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
            f"codex exec failed (exit {result.returncode})\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def prepare_workspace(add_cleanup):
    codex_cmd = os.environ.get("CODEX_E2E_CMD", "codex")
    _require_tool(codex_cmd)
    _require_tool("git")

    tmp = tempfile.TemporaryDirectory()
    add_cleanup(tmp.cleanup)
    tmp_path = Path(tmp.name)

    codex_home = tmp_path / "codex_home"
    auth_key = _ensure_auth(codex_home)
    _copy_config(codex_home)
    _install_skills(codex_home)

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
