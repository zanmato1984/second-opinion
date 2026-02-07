from __future__ import annotations

from typing import Iterable, List, Set, Tuple

from core.model import Finding


def merge_findings(findings: Iterable[Finding]) -> List[Finding]:
    merged: List[Finding] = []
    seen: Set[Tuple[str, str, str, str]] = set()
    for finding in findings:
        key = (
            finding.rule_id,
            finding.file,
            finding.line_range,
            finding.message,
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(finding)
    return merged
