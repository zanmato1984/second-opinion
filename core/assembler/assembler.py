from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from core.diff_parser import Diff
from core.model import Reviewer
from core.selector.selector import path_in_scope


@dataclass(frozen=True)
class PromptBundle:
    reviewer: Reviewer
    prompt: str
    added_lines_by_file: Dict[str, List[Tuple[int, str]]]

    def to_dict(self) -> dict:
        files = []
        for path, lines in self.added_lines_by_file.items():
            files.append(
                {
                    "path": path,
                    "lines": [{"line": line_no, "text": text} for line_no, text in lines],
                }
            )
        return {
            "reviewer": self.reviewer.id,
            "display_name": self.reviewer.display_name,
            "prompt": self.prompt,
            "files": files,
        }


def _load_reviewer_prompt(reviewer: Reviewer) -> str:
    if reviewer.path is None:
        return ""
    prompt_path = Path(reviewer.path) / "prompt.md"
    if not prompt_path.exists():
        return ""
    return prompt_path.read_text().strip()


def _build_prompt(reviewer: Reviewer, added_lines_by_file: Dict[str, List[Tuple[int, str]]]) -> str:
    sections: List[str] = []
    reviewer_prompt = _load_reviewer_prompt(reviewer)
    if reviewer_prompt:
        sections.append(reviewer_prompt)
    sections.append("Review the following diff slice:")
    for path, lines in added_lines_by_file.items():
        sections.append(f"File: {path}")
        for line_no, text in lines:
            sections.append(f"+{line_no}: {text}")
    return "\n".join(sections).strip()


def collect_added_lines(reviewer: Reviewer, diff: Diff) -> Dict[str, List[Tuple[int, str]]]:
    included: Dict[str, List[Tuple[int, str]]] = {}
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


def assemble_prompts(reviewers: Iterable[Reviewer], diff: Diff) -> List[PromptBundle]:
    bundles: List[PromptBundle] = []
    for reviewer in reviewers:
        added_lines = collect_added_lines(reviewer, diff)
        if not added_lines:
            continue
        prompt = _build_prompt(reviewer, added_lines)
        bundles.append(
            PromptBundle(
                reviewer=reviewer,
                prompt=prompt,
                added_lines_by_file=added_lines,
            )
        )
    return bundles
