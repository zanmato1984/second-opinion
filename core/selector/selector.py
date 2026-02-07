from __future__ import annotations

from dataclasses import dataclass
import fnmatch
from typing import List

from core.diff_parser import Diff
from core.model import Reviewer
from core.registry import Registry


@dataclass
class Selection:
    reviewer: Reviewer
    reason: str


def matches_paths(paths: List[str], includes: List[str], excludes: List[str]) -> bool:
    if not paths:
        return not includes
    def match_any(patterns: List[str], path: str) -> bool:
        return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)

    matched = False
    for path in paths:
        if excludes and match_any(excludes, path):
            continue
        if not includes:
            matched = True
            break
        if match_any(includes, path):
            matched = True
            break
    return matched


def path_in_scope(path: str, includes: List[str], excludes: List[str]) -> bool:
    if excludes and any(fnmatch.fnmatch(path, pattern) for pattern in excludes):
        return False
    if not includes:
        return True
    return any(fnmatch.fnmatch(path, pattern) for pattern in includes)


def select_reviewers(diff: Diff, registry: Registry, repo: str) -> List[Selection]:
    selections: List[Selection] = []
    paths = diff.file_paths()
    for reviewer in registry.reviewers.values():
        scope = reviewer.scopes
        if scope.repos and repo not in scope.repos:
            continue
        if not matches_paths(paths, scope.paths_include, scope.paths_exclude):
            continue
        reason = "scope match"
        selections.append(Selection(reviewer=reviewer, reason=reason))
    return selections
