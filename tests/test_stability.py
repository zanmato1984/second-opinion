from __future__ import annotations

from pathlib import Path

from core.orchestrator import Orchestrator, OrchestratorConfig
from core.registry import load_registry


def test_stability_repeatable_results() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    registry = load_registry(repo_root)
    orchestrator = Orchestrator(
        registry,
        OrchestratorConfig(
            repo_root=repo_root, schema_path=repo_root / "schema" / "review_output.schema.json"
        ),
    )
    diff_path = repo_root / "tests" / "golden_prs" / "GP0001_deadlock_cpp" / "patch.diff"
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
