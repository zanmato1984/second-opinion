from __future__ import annotations

import re
from typing import Dict, List, Tuple

from core.diff_parser import Diff
from core.model import Finding, Reviewer
from core.selector.selector import path_in_scope


def run_reviewer(reviewer: Reviewer, diff: Diff) -> List[Finding]:
    added_lines_by_file = {
        file_diff.path: file_diff.added_lines() for file_diff in diff.files
    }
    return run_reviewer_on_added_lines(reviewer, added_lines_by_file)


def run_reviewer_on_added_lines(
    reviewer: Reviewer, added_lines_by_file: Dict[str, List[Tuple[int, str]]]
) -> List[Finding]:
    findings: List[Finding] = []
    scope = reviewer.scopes
    for path, added_lines in added_lines_by_file.items():
        if not path_in_scope(path, scope.paths_include, scope.paths_exclude):
            continue
        if not added_lines:
            continue
        line_numbers = [line_no for line_no, _ in added_lines]
        text = "\n".join([line for _, line in added_lines])
        if not text:
            continue
        for rule in reviewer.rules:
            if not rule.pattern:
                continue
            try:
                regex = re.compile(rule.pattern, re.MULTILINE | re.DOTALL)
            except re.error:
                continue
            for match in regex.finditer(text):
                start_idx = text[: match.start()].count("\n")
                end_idx = text[: match.end()].count("\n")
                start_idx = min(start_idx, len(line_numbers) - 1)
                end_idx = min(end_idx, len(line_numbers) - 1)
                start_line = line_numbers[start_idx]
                end_line = line_numbers[end_idx]
                line_range = (
                    f"{start_line}" if start_line == end_line else f"{start_line}-{end_line}"
                )
                findings.append(
                    Finding(
                        reviewer=reviewer.id,
                        rule_id=rule.id,
                        file=path,
                        line_range=line_range,
                        severity=rule.severity,
                        message=rule.message,
                        suggestion=rule.suggestion,
                        confidence=rule.confidence,
                    )
                )
    return findings
