from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import List

from core.model import Reviewer
from core.registry.registry import Registry


_TAG_RE = re.compile(r"^[a-zA-Z0-9_.-]+:[a-zA-Z0-9_.-]+$")


@dataclass(frozen=True)
class ValidationError:
    source: str
    message: str


def validate_reviewer_files(reviewer: Reviewer) -> List[ValidationError]:
    errors: List[ValidationError] = []
    if reviewer.path is None:
        return errors
    base = Path(reviewer.path)
    config_path = base / "reviewer.yaml"
    if not config_path.exists():
        errors.append(ValidationError(reviewer.id, "Missing reviewer.yaml"))
    prompt_path = base / "prompt.md"
    if not prompt_path.exists():
        errors.append(ValidationError(reviewer.id, "Missing prompt.md"))
    return errors


def validate_reviewer(reviewer: Reviewer) -> List[ValidationError]:
    errors: List[ValidationError] = []
    if not reviewer.owners:
        errors.append(ValidationError(reviewer.id, "At least one owner is required"))
    if not reviewer.display_name:
        errors.append(ValidationError(reviewer.id, "display_name is required"))
    if not reviewer.type:
        errors.append(ValidationError(reviewer.id, "type is required"))

    rule_ids = set()
    for rule in reviewer.rules:
        if rule.id in rule_ids:
            errors.append(ValidationError(reviewer.id, f"Duplicate rule id '{rule.id}'"))
        rule_ids.add(rule.id)
        if not (0.0 <= rule.confidence <= 1.0):
            errors.append(
                ValidationError(
                    reviewer.id, f"Rule '{rule.id}' confidence must be between 0 and 1"
                )
            )
        if rule.pattern:
            try:
                re.compile(rule.pattern)
            except re.error as exc:
                errors.append(
                    ValidationError(
                        reviewer.id, f"Rule '{rule.id}' has invalid pattern: {exc}"
                    )
                )

    for tag in reviewer.tags:
        if not _TAG_RE.match(tag):
            errors.append(
                ValidationError(reviewer.id, f"Tag '{tag}' must follow key:value format")
            )

    errors.extend(validate_reviewer_files(reviewer))
    return errors


def validate_registry(registry: Registry) -> List[ValidationError]:
    errors: List[ValidationError] = []
    for reviewer in registry.reviewers.values():
        errors.extend(validate_reviewer(reviewer))
    for collection in registry.collections.values():
        for reviewer_id in collection.reviewers:
            if reviewer_id not in registry.reviewers:
                errors.append(
                    ValidationError(
                        collection.id,
                        f"Collection references unknown reviewer '{reviewer_id}'",
                    )
                )
    return errors
