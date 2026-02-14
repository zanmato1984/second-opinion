# Windtalker expert criteria

- rule_id: WINDTALKER-SEM-001
  description: |
    Treat TiDB/MySQL semantics as the contract. If a change can alter observable behavior
    (type inference, NULL propagation, time/collation, pushdown eligibility, warnings, error class),
    require an explicit proof and compatibility tests that demonstrate parity.
  tags:
    - risk:correctness
    - risk:compat
    - theme:testing
  rationale: Most semantic regressions look harmless in code but become user-visible behavior drift.

- rule_id: WINDTALKER-TYPE-002
  description: |
    For expression/function changes, verify type/nullable correctness end-to-end:
    unsigned vs signed merges, decimal precision/scale, flen/decimal/precision limits, cast targets
    (e.g., `DATETIME` vs `TIMESTAMP`), and overflow/truncation behavior. If any of these change,
    add targeted tests that cover boundary values and warning counts.
  tags:
    - component:tidb/expression
    - component:tiflash/compute
    - risk:correctness
    - risk:compat
    - theme:testing
  rationale: Type and cast drift causes silent incorrect results and MySQL compatibility breaks.

- rule_id: WINDTALKER-NULL-003
  description: |
    Validate NULL propagation and three-valued logic in joins/filters/aggs/windows, including
    explicit handling for NULL-equality (`<=>`) and "empty input" behavior that affects result
    nullability. For nullable columns, ensure null maps are merged/propagated consistently.
  tags:
    - component:tidb/execution
    - component:tidb/expression
    - component:tiflash/compute
    - risk:correctness
    - risk:compat
  rationale: NULL semantics are easy to break and hard to detect without systematic checks.

- rule_id: WINDTALKER-TZCOLL-004
  description: |
    For timezone/collation-sensitive logic, confirm evaluation happens at the correct granularity
    (per-row vs per-block/chunk) and uses the correct session/global settings. New collation paths
    must be correctly gated and covered by tests.
  tags:
    - component:tidb/sql-infra
    - component:tidb/expression
    - risk:compat
    - risk:correctness
    - theme:testing
  rationale: Timezone/collation regressions are high-impact compatibility issues and often slip through review.

- rule_id: WINDTALKER-PUSHDOWN-005
  description: |
    For pushdown/DAG/MPP-related changes, verify "pushdown is only correct when semantics are identical":
    check PB conversion, store-type gating, and DNF behavior (if any clause is not pushdown-safe, ensure
    overall behavior matches TiDB unless explicitly changed). Confirm schema/output field types are derived
    from the correct executor order.
  tags:
    - component:tidb/planner
    - component:tidb/execution
    - component:tikv/coprocessor
    - component:tiflash/compute
    - risk:correctness
    - risk:compat
  rationale: Incorrect pushdown yields silent wrong results and is extremely difficult to diagnose post-fact.

- rule_id: WINDTALKER-JOINAGG-006
  description: |
    For join/agg/window changes, verify correctness and stability across variants:
    build/probe side selection, join schema, and behavior across join types; stream vs hash aggregation
    changes must be intentional and tested; window registration/args must not be mixed into aggregate
    semantics without strong justification and tests.
  tags:
    - component:tidb/planner
    - component:tidb/execution
    - component:tiflash/compute
    - risk:correctness
    - risk:compat
    - theme:testing
  rationale: Join/agg/window semantics are complex; small drifts create large correctness gaps.

- rule_id: WINDTALKER-MPP-007
  description: |
    For MPP/pipeline changes, ensure cancellation and partial failure handling are safe and deterministic
    across all stores. Logs/metrics must preserve task identity (e.g., MPP task id, query ts) without
    duplication, so failures are observable and actionable.
  tags:
    - component:tidb/execution
    - component:tiflash/compute
    - risk:concurrency
    - risk:ops
    - theme:observability
  rationale: MPP issues are often production-only; correctness requires both safe behavior and strong observability.

- rule_id: WINDTALKER-PERF-008
  description: |
    Treat the normal hot path as sacred. Question changes that add copies/allocations/decoding on the
    success path just to handle rare errors or de-flake tests; prefer restructuring so extra cost happens
    only on the error/corner-case path. When output size is fixed (e.g., UUID string), prefer precise
    reservation/preallocation using the known size.
  tags:
    - component:tidb/execution
    - component:tidb/expression
    - component:tiflash/compute
    - risk:perf
  rationale: Small hot-path regressions can dominate cluster cost; error-path-only overhead is usually acceptable.
