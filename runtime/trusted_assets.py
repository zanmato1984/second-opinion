"""Pinned, read-only production assets. No project/CWD discovery or root override."""

from pathlib import Path

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
