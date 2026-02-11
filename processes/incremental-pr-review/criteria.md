# Incremental PR review process

- workflow_id: XHY-WORKFLOW-PR-001
  name: Scope-aware PR review (first / incremental / verification)
  body: |
    Goal: produce an evidence-based, attributable review that is efficient for iterative updates.

    Step 0) Determine review scope
    - First review: no prior baseline in this conversation.
    - Incremental review: new commits exist after a previously reviewed baseline.
    - Targeted verification: verify specific previously raised items only.

    Step 1) Collect minimal-but-sufficient evidence
    - Prefer PR artifacts when available (description, changed files, diff).
    - For incremental review, focus only on the new diff since the last baseline.
    - Run targeted checks/tests when feasible; avoid broad test runs by default.

    Step 2) Review dimensions (always)
    - Correctness: logic, error handling, cleanup paths.
    - Engineering risk: leaks, races, deadlocks, unsafe defaults.
    - Compatibility (when contracts change): defaults, units, upgrade/rollback behavior.
    - Performance (non-blocking by default): avoid unbounded reads/copies and extra I/O.

    Step 3) Produce findings in review.md and review.json
    - Write review.md in the user's preferred language.
    - Each finding should include:
      - location (file + lines)
      - severity (low/medium/high/critical)
      - message (problem + suggested action + how to verify)
    - Keep findings scoped to the selected rules/policies and the provided diff.
