from __future__ import annotations

from typing import Iterable, List

from core.assembler.assembler import PromptBundle
from core.model import Finding
from core.orchestrator.runner import run_reviewer_on_added_lines


def run_final_review(bundles: Iterable[PromptBundle]) -> List[Finding]:
    findings: List[Finding] = []
    for bundle in bundles:
        findings.extend(
            run_reviewer_on_added_lines(bundle.reviewer, bundle.added_lines_by_file)
        )
    return findings
