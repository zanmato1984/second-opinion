from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from jsonschema import Draft7Validator

from core.diff_parser import parse_unified_diff
from core.assembler.assembler import assemble_prompts
from core.final_review.final_review import run_final_review
from core.merger.merger import merge_findings
from core.model import Finding, ReviewReport
from core.registry import Registry
from core.selector.selector import ReviewerSelector, expand_collections


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
        selector = ReviewerSelector()
        selections = selector.select(diff, self._registry, repo)
        selected_reviewers = [selection.reviewer for selection in selections]
        selected_reviewers = expand_collections(
            selected_reviewers, self._registry, list(collection_ids) if collection_ids else None
        )

        bundles = assemble_prompts(selected_reviewers, diff)
        findings = run_final_review(bundles)

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

    def _validate(self, report: ReviewReport) -> None:
        errors = sorted(self._schema_validator.iter_errors(report.to_dict()), key=str)
        if errors:
            message = "; ".join(error.message for error in errors)
            raise ValueError(f"Output schema validation failed: {message}")
