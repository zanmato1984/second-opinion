from __future__ import annotations

from core.selector.selector import matches_paths, path_in_scope


def test_matches_paths_with_includes_and_excludes() -> None:
    paths = ["src/storage/file.cpp", "docs/readme.md"]
    assert matches_paths(paths, ["**/storage/**"], []) is True
    assert matches_paths(paths, ["**/storage/**"], ["**/*.md"]) is True
    assert matches_paths(paths, ["**/storage/**"], ["**/storage/**"]) is False


def test_path_in_scope() -> None:
    assert path_in_scope("docs/readme.md", ["**/*.md"], []) is True
    assert path_in_scope("docs/readme.md", ["**/*.md"], ["docs/**"]) is False
