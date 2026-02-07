from __future__ import annotations

import json
from typing import Iterable, List

from core.assembler.assembler import PromptBundle, build_final_prompt
from core.llm import LLMBackend, LLMRequest
from core.model import Finding


class LLMFinalReviewer:
    def __init__(self, backend: LLMBackend) -> None:
        self._backend = backend
        self.mode = "llm"

    def review(self, bundles: Iterable[PromptBundle]) -> List[Finding]:
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


def run_final_review(bundles: Iterable[PromptBundle], backend: LLMBackend) -> List[Finding]:
    reviewer = LLMFinalReviewer(backend)
    return reviewer.review(bundles)
