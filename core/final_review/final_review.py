from __future__ import annotations

import json
from typing import Iterable, List

from core.assembler.assembler import PromptBundle, build_final_prompt
from core.llm import LLMBackend, LLMRequest
from core.model import Finding
from core.orchestrator.runner import run_reviewer_on_added_lines


class RuleFinalReviewer:
    mode = "rule"

    def review(self, bundles: Iterable[PromptBundle]) -> List[Finding]:
        findings: List[Finding] = []
        for bundle in bundles:
            findings.extend(
                run_reviewer_on_added_lines(bundle.reviewer, bundle.added_lines_by_file)
            )
        return findings


class LLMFinalReviewer:
    def __init__(self, backend: LLMBackend | None = None) -> None:
        self._backend = backend
        self._fallback = RuleFinalReviewer()
        self.mode = "llm" if backend is not None else "fallback: rule"

    def review(self, bundles: Iterable[PromptBundle]) -> List[Finding]:
        if self._backend is None:
            return self._fallback.review(bundles)

        prompt = build_final_prompt(bundles)
        response = self._backend.complete(LLMRequest(prompt=prompt))
        raw_findings = json.loads(response)
        findings: List[Finding] = []
        for item in raw_findings:
            findings.append(
                Finding(
                    reviewer=item["reviewer"],
                    rule_id=item["rule_id"],
                    file=item["file"],
                    line_range=item["line_range"],
                    severity=item["severity"],
                    message=item["message"],
                    suggestion=item.get("suggestion"),
                    confidence=float(item["confidence"]),
                )
            )
        return findings


def run_final_review(bundles: Iterable[PromptBundle]) -> List[Finding]:
    reviewer = RuleFinalReviewer()
    return reviewer.review(bundles)
