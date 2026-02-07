from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from core.model import Collection, Reviewer, ReviewerConfigError, build_reviewer


@dataclass
class Registry:
    reviewers: Dict[str, Reviewer]
    collections: Dict[str, Collection]

    def get_reviewer(self, reviewer_id: str) -> Reviewer:
        return self.reviewers[reviewer_id]

    def get_collection(self, collection_id: str) -> Collection:
        return self.collections[collection_id]


class RegistryLoadError(RuntimeError):
    pass


def _load_yaml(path: Path) -> dict:
    try:
        raw = yaml.safe_load(path.read_text())
    except Exception as exc:  # pragma: no cover - rare
        raise RegistryLoadError(f"Failed to parse {path}: {exc}") from exc
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise RegistryLoadError(f"Expected mapping in {path}")
    return raw


def load_reviewers(reviewers_root: Path) -> Dict[str, Reviewer]:
    reviewers: Dict[str, Reviewer] = {}
    if not reviewers_root.exists():
        return reviewers
    for entry in reviewers_root.iterdir():
        if not entry.is_dir():
            continue
        config_path = entry / "reviewer.yaml"
        if not config_path.exists():
            continue
        raw = _load_yaml(config_path)
        try:
            reviewer = build_reviewer(raw, path=entry)
        except ReviewerConfigError as exc:
            raise RegistryLoadError(f"Invalid reviewer at {entry}: {exc}") from exc
        if reviewer.id in reviewers:
            raise RegistryLoadError(f"Duplicate reviewer id '{reviewer.id}'")
        reviewers[reviewer.id] = reviewer
    return reviewers


def load_collections(collections_root: Path) -> Dict[str, Collection]:
    collections: Dict[str, Collection] = {}
    if not collections_root.exists():
        return collections
    for entry in collections_root.iterdir():
        if entry.suffix not in {".yaml", ".yml"}:
            continue
        raw = _load_yaml(entry)
        collection_id = raw.get("id") or entry.stem
        reviewers = raw.get("reviewers") or []
        if not isinstance(reviewers, list):
            raise RegistryLoadError(f"Collection {entry} reviewers must be a list")
        collection = Collection(
            id=collection_id,
            reviewers=list(reviewers),
            preferred_types=list(raw.get("preferred_types") or []),
        )
        if collection.id in collections:
            raise RegistryLoadError(f"Duplicate collection id '{collection.id}'")
        collections[collection.id] = collection
    return collections


def load_registry(repo_root: Path) -> Registry:
    reviewers = load_reviewers(repo_root / "reviewers")
    collections = load_collections(repo_root / "collections")
    return Registry(reviewers=reviewers, collections=collections)
