from __future__ import annotations

import textwrap

from core.diff_parser import parse_unified_diff
from core.model import Budget, Reviewer, Scope
from core.orchestrator.orchestrator import build_prompt_and_lines


def test_prompt_budget_truncation() -> None:
    diff_text = textwrap.dedent(
        """
        diff --git a/src/foo.cpp b/src/foo.cpp
        index 1111111..2222222 100644
        --- a/src/foo.cpp
        +++ b/src/foo.cpp
        @@ -1,3 +1,5 @@
         int main() {
        +  int a = 0;
        +  int b = 1;
           return 0;
         }
        """
    ).strip()

    reviewer = Reviewer(
        id="test",
        type="domain",
        owners=["tester"],
        display_name="Test",
        description="",
        scopes=Scope(repos=[], paths_include=["**/*.cpp"], paths_exclude=[]),
        tags=[],
        budget=Budget(max_tokens=8),
        rules=[],
        path=None,
    )

    diff = parse_unified_diff(diff_text)
    prompt_text, included, tokens_used, truncated = build_prompt_and_lines(
        reviewer, diff, reviewer.budget.max_tokens
    )

    assert truncated is True
    assert tokens_used <= reviewer.budget.max_tokens
    assert "src/foo.cpp" in included
    assert len(included["src/foo.cpp"]) == 1
    assert "+1:" in prompt_text or "+2:" in prompt_text
