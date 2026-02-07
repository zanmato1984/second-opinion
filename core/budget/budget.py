from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from core.model import Reviewer


@dataclass
class BudgetedInput:
    reviewer: Reviewer
    text: str
    estimated_tokens: int
    max_tokens: Optional[int]
    truncated: bool = False


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return len(text.split())


def truncate_text(text: str, max_tokens: int) -> Tuple[str, bool]:
    tokens = text.split()
    if len(tokens) <= max_tokens:
        return text, False
    truncated = " ".join(tokens[:max_tokens])
    return truncated, True


def apply_budget(
    reviewer_inputs: Dict[str, str],
    reviewers: Dict[str, Reviewer],
    max_tokens: Optional[int],
) -> List[BudgetedInput]:
    results: List[BudgetedInput] = []
    remaining = max_tokens
    for reviewer_id, text in reviewer_inputs.items():
        reviewer = reviewers[reviewer_id]
        per_reviewer_limit = reviewer.budget.max_tokens
        effective_limit: Optional[int]
        if per_reviewer_limit is None and remaining is None:
            effective_limit = None
        elif per_reviewer_limit is None:
            effective_limit = remaining
        elif remaining is None:
            effective_limit = per_reviewer_limit
        else:
            effective_limit = min(per_reviewer_limit, remaining)

        estimated = estimate_tokens(text)
        truncated = False
        if effective_limit is not None:
            text, truncated = truncate_text(text, effective_limit)
            estimated = estimate_tokens(text)
            remaining = max(0, remaining - estimated) if remaining is not None else None
            if remaining == 0:
                results.append(
                    BudgetedInput(
                        reviewer=reviewer,
                        text=text,
                        estimated_tokens=estimated,
                        max_tokens=effective_limit,
                        truncated=truncated,
                    )
                )
                break
        results.append(
            BudgetedInput(
                reviewer=reviewer,
                text=text,
                estimated_tokens=estimated,
                max_tokens=effective_limit,
                truncated=truncated,
            )
        )
    return results
