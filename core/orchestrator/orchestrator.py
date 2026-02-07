from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from jsonschema import Draft7Validator

from core.diff_parser import Diff, parse_unified_diff
from core.merger.merger import merge_findings
from core.model import Finding, ReviewReport, Reviewer
from core.orchestrator.runner import run_reviewer_on_added_lines
from core.registry import Registry
from core.selector.selector import path_in_scope, select_reviewers


@dataclass
class OrchestratorConfig:
    repo_root: Path
    schema_path: Path


class Orchestrator:
    def __init__(self, registry: Registry, config: OrchestratorConfig) -> None:
        self._registry = registry
        self._config = config
        self._schema_validator = Draft7Validator(self._load_schema(config.schema_path))

    @staticmethod
    def _load_schema(path: Path) -> dict:
        import json

        return json.loads(path.read_text())

    def run(
        self,
        diff_text: str,
        repo: str,
        collection_ids: Optional[Iterable[str]] = None,
    ) -> ReviewReport:
        diff = parse_unified_diff(diff_text)
        selections = select_reviewers(diff, self._registry, repo)
        selected_reviewers = [selection.reviewer for selection in selections]
        selected_reviewers = self._expand_collections(selected_reviewers, collection_ids)

        findings: List[Finding] = []
        for reviewer in selected_reviewers:
            added_lines_by_file = collect_added_lines(reviewer, diff)
            if not added_lines_by_file:
                continue
            findings.extend(run_reviewer_on_added_lines(reviewer, added_lines_by_file))

        merged_findings = merge_findings(findings)
        report = ReviewReport(
            repo=repo,
            reviewers=[reviewer.id for reviewer in selected_reviewers],
            findings=merged_findings,
            stats={
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_reviewers": len(selected_reviewers),
                "total_findings": len(merged_findings),
            },
        )
        self._validate(report)
        return report

    def _expand_collections(
        self, reviewers: List[Reviewer], collection_ids: Optional[Iterable[str]]
    ) -> List[Reviewer]:
        if not collection_ids:
            return reviewers
        reviewers_by_id = {reviewer.id: reviewer for reviewer in reviewers}
        preferred_types: List[str] = []
        for collection_id in collection_ids:
            collection = self._registry.collections.get(collection_id)
            if not collection:
                raise ValueError(f"Unknown collection '{collection_id}'")
            for reviewer_id in collection.reviewers:
                reviewer = self._registry.reviewers.get(reviewer_id)
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

    def _validate(self, report: ReviewReport) -> None:
        errors = sorted(self._schema_validator.iter_errors(report.to_dict()), key=str)
        if errors:
            message = "; ".join(error.message for error in errors)
            raise ValueError(f"Output schema validation failed: {message}")


def collect_added_lines(
    reviewer: Reviewer, diff: Diff
) -> Dict[str, List[tuple[int, str]]]:
    included: Dict[str, List[tuple[int, str]]] = {}

    for file_diff in diff.files:
        if not path_in_scope(
            file_diff.path, reviewer.scopes.paths_include, reviewer.scopes.paths_exclude
        ):
            continue
        added_lines = file_diff.added_lines()
        if not added_lines:
            continue
        included[file_diff.path] = list(added_lines)

    return included
