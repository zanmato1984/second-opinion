from __future__ import annotations

import json
import fnmatch
from typing import Any, Dict, List

from core.llm.backend import LLMBackend, LLMRequest


def _matches_paths(paths: List[str], includes: List[str], excludes: List[str]) -> bool:
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


def _extract_context(prompt: str) -> Dict[str, Any] | None:
    marker = "Context:\n"
    if marker not in prompt:
        return None
    payload = prompt.split(marker, 1)[1].strip()
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def _select_from_prompt(prompt: str) -> List[str]:
    context = _extract_context(prompt)
    if not context:
        return []
    repo = context.get("repo")
    changed_files = context.get("changed_files", [])
    reviewers = context.get("reviewers", [])
    selected: List[str] = []
    for reviewer in reviewers:
        scopes = reviewer.get("scopes", {})
        repos = scopes.get("repos") or []
        if repos and repo not in repos:
            continue
        includes = scopes.get("paths_include") or []
        excludes = scopes.get("paths_exclude") or []
        if not _matches_paths(changed_files, includes, excludes):
            continue
        selected.append(reviewer.get("id"))
    return [rid for rid in selected if rid]


class MockBackend(LLMBackend):
    def __init__(
        self,
        selector_output: List[str] | None = None,
        final_output: List[Dict[str, Any]] | None = None,
    ) -> None:
        self._selector_output = selector_output
        self._final_output = final_output

    def complete(self, request: LLMRequest) -> str:
        if "Select the best reviewers" in request.prompt:
            if self._selector_output is not None:
                return json.dumps(self._selector_output)
            return json.dumps(_select_from_prompt(request.prompt))

        if "You are the final review agent" in request.prompt:
            if self._final_output is not None:
                return json.dumps(self._final_output)
            return "[]"

        return "[]"
