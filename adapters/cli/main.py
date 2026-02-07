from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.assembler import assemble_prompts, build_final_prompt
from core.diff_parser import parse_unified_diff
from core.orchestrator import Orchestrator, OrchestratorConfig
from core.registry import load_registry
from core.selector import ReviewerSelector, expand_collections


def _read_diff(path: str | None) -> str:
    if path is None or path == "-":
        return sys.stdin.read()
    return Path(path).read_text()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="second-opinion",
        description="Run Second Opinion review pipeline against a diff.",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("review", help="Run the full review pipeline (default)")
    subparsers.add_parser("select", help="Select reviewers based on metadata/tags")
    subparsers.add_parser("assemble", help="Assemble reviewer prompts deterministically")
    parser.add_argument("--repo", required=True, help="Repository identifier (e.g., pingcap/tidb)")
    parser.add_argument("--diff", default="-", help="Path to unified diff (or '-' for stdin)")
    parser.add_argument(
        "--collections",
        default="",
        help="Comma-separated collection IDs to include",
    )
    parser.add_argument(
        "--reviewers",
        default="",
        help="Comma-separated reviewer IDs (used by assemble)",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing reviewers/ and collections/",
    )
    parser.add_argument(
        "--schema",
        default="schema/review_output.schema.json",
        help="Path to JSON schema for validation",
    )
    parser.add_argument(
        "--output",
        default="-",
        help="Output path for JSON report (or '-' for stdout)",
    )
    return parser


def _parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root)
    registry = load_registry(repo_root)
    schema_path = Path(args.schema)
    if not schema_path.is_absolute():
        schema_path = repo_root / schema_path
    config = OrchestratorConfig(repo_root=repo_root, schema_path=schema_path)
    orchestrator = Orchestrator(registry, config)

    diff_text = _read_diff(args.diff)
    if not diff_text.strip():
        raise SystemExit("Diff input is empty")

    collections = _parse_csv(args.collections)
    command = args.command or "review"

    if command == "select":
        diff = parse_unified_diff(diff_text)
        selector = ReviewerSelector()
        selections = selector.select(diff, registry, args.repo)
        reviewers = [selection.reviewer for selection in selections]
        reviewers = expand_collections(reviewers, registry, collections or None)
        payload = {
            "reviewers": [reviewer.id for reviewer in reviewers],
            "selections": [selection.to_dict() for selection in selections],
            "collections": collections,
        }
        output_json = json.dumps(payload, indent=2, sort_keys=True)
    elif command == "assemble":
        diff = parse_unified_diff(diff_text)
        reviewer_ids = _parse_csv(args.reviewers)
        if reviewer_ids:
            reviewers = []
            for reviewer_id in reviewer_ids:
                reviewer = registry.reviewers.get(reviewer_id)
                if reviewer is None:
                    raise SystemExit(f"Unknown reviewer '{reviewer_id}'")
                reviewers.append(reviewer)
        else:
            selector = ReviewerSelector()
            selections = selector.select(diff, registry, args.repo)
            reviewers = [selection.reviewer for selection in selections]
        reviewers = expand_collections(reviewers, registry, collections or None)
        bundles = assemble_prompts(reviewers, diff)
        payload = {
            "bundles": [bundle.to_dict() for bundle in bundles],
            "final_prompt": build_final_prompt(bundles),
        }
        output_json = json.dumps(payload, indent=2, sort_keys=True)
    else:
        report = orchestrator.run(
            diff_text=diff_text,
            repo=args.repo,
            collection_ids=collections if collections else None,
        )
        output_json = json.dumps(report.to_dict(), indent=2, sort_keys=True)

    if args.output == "-":
        print(output_json)
    else:
        Path(args.output).write_text(output_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
