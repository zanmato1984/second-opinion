"""Pinned, read-only production assets. No project/CWD discovery or root override."""

from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ("experts", "processes", "policies", "fragments", "prompts", "schemas")
SAMPLES = {"experts/foo", "processes/foo", "policies/foo.yaml", "fragments/foo.md"}
LIMIT = 4 * 1024 * 1024


def _within(path, parent):
    return path == parent or parent in path.parents


def verify_root(review_root):
    root = ROOT.resolve(strict=True)
    reviewed = Path(review_root).resolve(strict=True)
    if not reviewed.is_dir():
        raise ValueError("Review root must be a directory")
    if _within(root, reviewed) or _within(reviewed, root):
        raise PermissionError("Trusted installation and reviewed tree must be separate")
    if not (root / "taxonomy.md").is_file():
        raise ValueError("Trusted installation is incomplete; no fallback is allowed")
    for name in ("taxonomy.md", *DIRECTORIES):
        path = root / name
        if path.is_symlink() or not path.exists():
            raise ValueError("Missing or symlinked trusted asset")
    return root


def bundle(review_root):
    root = verify_root(review_root)
    paths = [root / "taxonomy.md"]
    for name in DIRECTORIES:
        for path in sorted((root / name).rglob("*")):
            relative = path.relative_to(root).as_posix()
            if any(relative == sample or relative.startswith(sample + "/") for sample in SAMPLES):
                continue
            if path.is_symlink():
                raise ValueError("Symlinked asset rejected")
            if path.is_file() and path.suffix in (".md", ".yaml", ".prompt", ".json"):
                paths.append(path)
    assets = {}
    total = 0
    for path in paths:
        with path.open("rb") as handle:
            data = handle.read(LIMIT + 1)
        total += len(data)
        if len(data) > LIMIT or total > LIMIT:
            raise ValueError("Trusted asset bundle exceeds size limit")
        assets[path.relative_to(root).as_posix()] = data.decode("utf-8")
    return {"asset_root": str(root), "assets": assets}


def compile_review(review_root, process="pr-review"):
    """Compile from pinned bytes, not a model's prompt/provenance assertions.

    This conservative reference mode includes every production expert. It does
    not use model-selected rules, priority, exclusive, or activation metadata.
    An explicit workflow cannot remove mandatory policies or output contracts.
    """
    if process not in ("pr-review", "review-branch"):
        raise ValueError("Unsupported review process")
    assets = bundle(review_root)["assets"]
    policies = sorted(path for path in assets if path.startswith("policies/") and path.endswith(".yaml"))
    required = ["policies/baseline-high-severity.yaml", "policies/github-side-effects.yaml",
                f"processes/{process}/criteria.md", "fragments/output-review-findings.md",
                "fragments/review-language-contract.md"]
    if any(path not in assets for path in required):
        raise ValueError("Trusted installation is missing mandatory review assets")
    experts = sorted(path for path in assets if path.startswith("experts/") and path.endswith("/criteria.md"))
    fragments = sorted(path for path in assets if path.startswith("fragments/") and path.endswith(".md"))
    paths = policies + [f"processes/{process}/criteria.md"] + experts + fragments
    # JSON framing preserves each complete asset verbatim without interpreting
    # headings, YAML priorities, or delimiter-like text as host configuration.
    criteria = [{"path": path, "text": assets[path]} for path in paths]
    prompt = json.dumps(criteria, ensure_ascii=True, separators=(",", ":"))
    return {"mode": "pinned-conservative-v1", "selected_processes": [process],
            "selected_experts": [path.split("/")[1] for path in experts],
            "rules_used": {path.split("/")[1]: re.findall(r"(?m)^- rule_id: ([A-Za-z0-9_-]+)\s*$", assets[path])
                           for path in experts},
            "selected_policies": [Path(path).stem for path in policies],
            "selection_rationale": {"user_override": process, "candidates": [],
                                    "primary_process": {"process": process, "reason": "Operator-selected trusted workflow"},
                                    "secondary_processes": [], "tie_breakers": [], "budget": "conservative-all"},
            "compiled_prompt": prompt,
            "provenance": [{"path": path, "sha256": hashlib.sha256(assets[path].encode()).hexdigest()}
                           for path in paths]}
