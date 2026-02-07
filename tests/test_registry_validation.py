from __future__ import annotations

from pathlib import Path

from core.registry import load_registry
from core.registry.validator import validate_registry


def test_registry_validation() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    registry = load_registry(repo_root)
    errors = validate_registry(registry)
    assert errors == [], [f"{err.source}: {err.message}" for err in errors]
