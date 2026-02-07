from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


SEVERITY_LEVELS = {"info", "low", "medium", "high", "critical"}


class ReviewerConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Scope:
    repos: List[str] = field(default_factory=list)
    paths_include: List[str] = field(default_factory=list)
    paths_exclude: List[str] = field(default_factory=list)




@dataclass(frozen=True)
class Rule:
    id: str
    severity: str
    message: str
    suggestion: Optional[str] = None
    pattern: Optional[str] = None
    confidence: float = 0.5


@dataclass(frozen=True)
class Reviewer:
    id: str
    type: str
    owners: List[str]
    display_name: str
    description: str
    scopes: Scope
    tags: List[str] = field(default_factory=list)
    rules: List[Rule] = field(default_factory=list)
    path: Optional[Path] = None


@dataclass(frozen=True)
class Finding:
    reviewer: str
    rule_id: str
    file: str
    line_range: str
    severity: str
    message: str
    suggestion: Optional[str]
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reviewer": self.reviewer,
            "rule_id": self.rule_id,
            "file": self.file,
            "line_range": self.line_range,
            "severity": self.severity,
            "message": self.message,
            "suggestion": self.suggestion,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class ReviewReport:
    repo: str
    reviewers: List[str]
    findings: List[Finding]
    stats: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "1.0",
            "repo": self.repo,
            "reviewers": self.reviewers,
            "findings": [finding.to_dict() for finding in self.findings],
            "stats": self.stats,
        }


@dataclass(frozen=True)
class Collection:
    id: str
    reviewers: List[str]
    preferred_types: List[str] = field(default_factory=list)


def _as_list(value: Optional[Iterable[str]]) -> List[str]:
    if not value:
        return []
    return list(value)


def build_scope(raw: Dict[str, Any]) -> Scope:
    return Scope(
        repos=_as_list(raw.get("repos")),
        paths_include=_as_list(raw.get("paths_include")),
        paths_exclude=_as_list(raw.get("paths_exclude")),
    )


def build_rules(raw: Optional[Iterable[Dict[str, Any]]]) -> List[Rule]:
    rules: List[Rule] = []
    if not raw:
        return rules
    for entry in raw:
        rule = Rule(
            id=str(entry.get("id", "")),
            severity=str(entry.get("severity", "")),
            message=str(entry.get("message", "")),
            suggestion=entry.get("suggestion"),
            pattern=entry.get("pattern"),
            confidence=float(entry.get("confidence", 0.5)),
        )
        if not rule.id:
            raise ReviewerConfigError("Rule id is required")
        if rule.severity not in SEVERITY_LEVELS:
            raise ReviewerConfigError(
                f"Rule '{rule.id}' uses invalid severity '{rule.severity}'"
            )
        rules.append(rule)
    return rules


def build_reviewer(raw: Dict[str, Any], path: Optional[Path] = None) -> Reviewer:
    reviewer_id = raw.get("id")
    if not reviewer_id:
        raise ReviewerConfigError("Reviewer id is required")
    reviewer_type = raw.get("type") or "domain"
    owners = _as_list(raw.get("owners"))
    display_name = raw.get("display_name") or reviewer_id
    description = raw.get("description") or ""
    scopes = build_scope(raw.get("scopes", {}))
    tags = _as_list(raw.get("tags"))
    rules = build_rules(raw.get("rules"))
    return Reviewer(
        id=reviewer_id,
        type=reviewer_type,
        owners=owners,
        display_name=display_name,
        description=description,
        scopes=scopes,
        tags=tags,
        rules=rules,
        path=path,
    )
