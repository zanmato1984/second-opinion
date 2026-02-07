from __future__ import annotations

from dataclasses import dataclass
import fnmatch
import json
from typing import List

from core.diff_parser import Diff
from core.model import Reviewer
from core.registry import Registry
from core.llm import LLMBackend, LLMRequest


@dataclass
class Selection:
    reviewer: Reviewer
    reason: str

    def to_dict(self) -> dict:
        return {
            "reviewer": self.reviewer.id,
            "display_name": self.reviewer.display_name,
            "reason": self.reason,
        }


def path_in_scope(path: str, includes: List[str], excludes: List[str]) -> bool:
    if excludes and any(fnmatch.fnmatch(path, pattern) for pattern in excludes):
        return False
    if not includes:
        return True
    return any(fnmatch.fnmatch(path, pattern) for pattern in includes)


def build_selector_prompt(diff: Diff, registry: Registry, repo: str) -> str:
    reviewers = []
    for reviewer in registry.reviewers.values():
        reviewers.append(
            {
                "id": reviewer.id,
                "type": reviewer.type,
                "owners": reviewer.owners,
                "display_name": reviewer.display_name,
                "description": reviewer.description,
                "scopes": {
                    "repos": reviewer.scopes.repos,
                    "paths_include": reviewer.scopes.paths_include,
                    "paths_exclude": reviewer.scopes.paths_exclude,
                },
                "tags": reviewer.tags,
            }
        )
    payload = {
        "repo": repo,
        "changed_files": diff.file_paths(),
        "reviewers": reviewers,
    }
    return (
        "Select the best reviewers for the diff based on scopes, metadata, and tags. "
        "Return a JSON array of reviewer ids.\n\n"
        f"Context:\n{json.dumps(payload, indent=2, sort_keys=True)}"
    )


class LLMReviewerSelector:
    def __init__(self, backend: LLMBackend) -> None:
        self._backend = backend
        self.mode = "llm"

    def select(self, diff: Diff, registry: Registry, repo: str) -> List[Selection]:
        prompt = build_selector_prompt(diff, registry, repo)
        response = self._backend.complete(LLMRequest(prompt=prompt))
        reviewer_ids = json.loads(response)
        selections: List[Selection] = []
        for reviewer_id in reviewer_ids:
            reviewer = registry.reviewers.get(reviewer_id)
            if reviewer is None:
                raise ValueError(f"LLM selected unknown reviewer '{reviewer_id}'")
            selections.append(Selection(reviewer=reviewer, reason="llm"))
        return selections


def expand_collections(
    reviewers: List[Reviewer], registry: Registry, collection_ids: List[str] | None
) -> List[Reviewer]:
    if not collection_ids:
        return reviewers
    reviewers_by_id = {reviewer.id: reviewer for reviewer in reviewers}
    preferred_types: List[str] = []
    for collection_id in collection_ids:
        collection = registry.collections.get(collection_id)
        if not collection:
            raise ValueError(f"Unknown collection '{collection_id}'")
        for reviewer_id in collection.reviewers:
            reviewer = registry.reviewers.get(reviewer_id)
            if not reviewer:
                raise ValueError(
                    f"Collection '{collection_id}' references unknown reviewer '{reviewer_id}'"
                )
            reviewers_by_id.setdefault(reviewer.id, reviewer)
        preferred_types.extend(collection.preferred_types)

    ordered = list(reviewers_by_id.values())
    if preferred_types:
        type_rank = {t: idx for idx, t in enumerate(preferred_types)}
        ordered.sort(key=lambda reviewer: type_rank.get(reviewer.type, len(type_rank)))
    return ordered
