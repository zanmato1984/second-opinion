# Ruoxi expert criteria

- rule_id: RUOXI-EXPR-001
  description: |
    For scalar builtin changes, confirm the vectorized implementation is updated
    in `*_vec.go`/`*_vec_generated.go`, `vectorized()` returns true when supported,
    and vectorized tests cover the new behavior.
  tags:
    - component:tidb/expression
    - theme:testing
    - risk:correctness
  rationale: Vectorized and row-based paths must stay in lock-step or behavior diverges.

- rule_id: RUOXI-EXPR-002
  description: |
    Ensure `eval*` and `vecEval*` are behaviorally equivalent for nulls, warnings,
    overflow/truncation, collation/timezone, and error types. Tests should compare
    per-row results and warning counts.
  tags:
    - component:tidb/expression
    - risk:compat
    - risk:correctness
  rationale: Subtle semantic drift causes correctness and compatibility issues.

- rule_id: RUOXI-EXPR-003
  description: |
    In vectorized code, avoid per-row evaluation/allocations: use column slices,
    pre-size result buffers, and respect selection vectors.
  tags:
    - component:tidb/expression
    - risk:perf
  rationale: Vectorized execution is a hot path and regressions are costly.
