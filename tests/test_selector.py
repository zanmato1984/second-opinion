from __future__ import annotations

import json
import textwrap
from pathlib import Path

from core.diff_parser import parse_unified_diff
from core.registry import load_registry
from core.selector.selector import build_selector_prompt, path_in_scope


def test_path_in_scope() -> None:
    assert path_in_scope("docs/readme.md", ["**/*.md"], []) is True
    assert path_in_scope("docs/readme.md", ["**/*.md"], ["docs/**"]) is False


def test_build_selector_prompt_contains_context() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    registry = load_registry(repo_root)
    diff_text = textwrap.dedent(
        """
        diff --git a/src/engine/worker.cpp b/src/engine/worker.cpp
        index 1111111..2222222 100644
        --- a/src/engine/worker.cpp
        +++ b/src/engine/worker.cpp
        @@ -1,1 +1,2 @@
        +int main() { return 0; }
        """
    ).strip()
    diff = parse_unified_diff(diff_text)
    prompt = build_selector_prompt(diff, registry, "pingcap/tidb")
    assert "Select the best reviewers" in prompt
    payload = json.loads(prompt.split("Context:\n", 1)[1])
    assert payload["repo"] == "pingcap/tidb"
    assert "src/engine/worker.cpp" in payload["changed_files"]
    assert any(r["id"] == "concurrency-safety" for r in payload["reviewers"])
