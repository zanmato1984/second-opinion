from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from jsonschema import Draft7Validator

from core.budget.budget import estimate_tokens
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
        max_tokens: Optional[int] = None,
    ) -> ReviewReport:
        diff = parse_unified_diff(diff_text)
        selections = select_reviewers(diff, self._registry, repo)
        selected_reviewers = [selection.reviewer for selection in selections]
        selected_reviewers = self._expand_collections(selected_reviewers, collection_ids)

        effective_global_budget = self._apply_collection_budget(max_tokens, collection_ids)

        findings: List[Finding] = []
        reviewer_tokens: Dict[str, int] = {}
        truncated_reviewers: List[str] = []

        remaining = effective_global_budget
        for reviewer in selected_reviewers:
            if remaining is not None and remaining <= 0:
                break
            per_limit = reviewer.budget.max_tokens
            if per_limit is None and remaining is None:
                effective_limit = None
            elif per_limit is None:
                effective_limit = remaining
            elif remaining is None:
                effective_limit = per_limit
            else:
                effective_limit = min(per_limit, remaining)

            _prompt_text, added_lines_by_file, tokens_used, truncated = build_prompt_and_lines(
                reviewer, diff, effective_limit
            )
            if tokens_used == 0 and not added_lines_by_file:
                continue
            reviewer_tokens[reviewer.id] = tokens_used
            if truncated:
                truncated_reviewers.append(reviewer.id)
            if remaining is not None:
                remaining = max(0, remaining - tokens_used)

            findings.extend(run_reviewer_on_added_lines(reviewer, added_lines_by_file))

        merged_findings = merge_findings(findings)
        report = ReviewReport(
            repo=repo,
            reviewers=[reviewer.id for reviewer in selected_reviewers],
            findings=merged_findings,
            stats={
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "reviewer_tokens": reviewer_tokens,
                "truncated_reviewers": truncated_reviewers,
                "total_reviewers": len(selected_reviewers),
                "total_findings": len(merged_findings),
                "max_tokens": effective_global_budget,
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

    def _apply_collection_budget(
        self, max_tokens: Optional[int], collection_ids: Optional[Iterable[str]]
    ) -> Optional[int]:
        if not collection_ids:
            return max_tokens
        effective = max_tokens
        for collection_id in collection_ids:
            collection = self._registry.collections.get(collection_id)
            if not collection or collection.max_tokens is None:
                continue
            if effective is None:
                effective = collection.max_tokens
            else:
                effective = min(effective, collection.max_tokens)
        return effective

    def _validate(self, report: ReviewReport) -> None:
        errors = sorted(self._schema_validator.iter_errors(report.to_dict()), key=str)
        if errors:
            message = "; ".join(error.message for error in errors)
            raise ValueError(f"Output schema validation failed: {message}")


def build_prompt_and_lines(
    reviewer: Reviewer, diff: Diff, max_tokens: Optional[int]
) -> Tuple[str, Dict[str, List[Tuple[int, str]]], int, bool]:
    prompt_lines: List[str] = []
    included: Dict[str, List[Tuple[int, str]]] = {}
    tokens_used = 0
    truncated = False

    for file_diff in diff.files:
        if not path_in_scope(
            file_diff.path, reviewer.scopes.paths_include, reviewer.scopes.paths_exclude
        ):
            continue
        added_lines = file_diff.added_lines()
        if not added_lines:
            continue
        header = f"File: {file_diff.path}"
        header_tokens = estimate_tokens(header)
        if max_tokens is not None and tokens_used + header_tokens > max_tokens:
            truncated = True
            break
        prompt_lines.append(header)
        tokens_used += header_tokens
        kept_lines: List[Tuple[int, str]] = []
        for line_no, text in added_lines:
            line_text = f"+{line_no}: {text}"
            line_tokens = estimate_tokens(line_text)
            if max_tokens is not None and tokens_used + line_tokens > max_tokens:
                truncated = True
                break
            prompt_lines.append(line_text)
            tokens_used += line_tokens
            kept_lines.append((line_no, text))
        if kept_lines:
            included[file_diff.path] = kept_lines
        if truncated:
            break

    return "\n".join(prompt_lines), included, tokens_used, truncated
