from __future__ import annotations

import json
from pathlib import Path

from core.llm import MockBackend
from core.orchestrator import Orchestrator, OrchestratorConfig
from core.registry import load_registry


def test_golden_pr_deadlock_cpp() -> None:
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

    report = orchestrator.run(diff_path.read_text(), repo="pingcap/tidb")
    assert report.to_dict()["findings"] == expected["findings"]
    assert "concurrency-safety" in report.to_dict()["reviewers"]
