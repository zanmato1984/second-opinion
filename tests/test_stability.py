from __future__ import annotations

from pathlib import Path

import json

from core.llm import MockBackend
from core.orchestrator import Orchestrator, OrchestratorConfig
from core.registry import load_registry


def test_stability_repeatable_results() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    registry = load_registry(repo_root)
    diff_path = repo_root / "tests" / "golden_prs" / "GP0001_deadlock_cpp" / "patch.diff"
    expected_path = (
        repo_root / "tests" / "golden_prs" / "GP0001_deadlock_cpp" / "expected.json"
    )
    expected = json.loads(expected_path.read_text())
    selector_backend = MockBackend(selector_output=["concurrency-safety"])
    final_backend = MockBackend(final_output=expected["findings"])
    orchestrator = Orchestrator(
        registry,
        OrchestratorConfig(
            repo_root=repo_root,
            schema_path=repo_root / "schema" / "review_output.schema.json",
            selector_backend=selector_backend,
            final_backend=final_backend,
        ),
    )
    diff_text = diff_path.read_text()

    def normalize(report: dict) -> dict:
        normalized = dict(report)
        stats = dict(normalized.get("stats", {}))
        stats.pop("generated_at", None)
        normalized["stats"] = stats
        return normalized

    outputs = [
        normalize(orchestrator.run(diff_text, repo="pingcap/tidb").to_dict())
        for _ in range(3)
    ]
    assert outputs[0] == outputs[1] == outputs[2]
