# xuhuaiyu expert criteria
#
# Notes:
# - Use only tags listed in taxonomy.md.
# - Keep rules atomic and attributable via rule_id.

- rule_id: XHY-PRR-001
  description: |
    Resource lifecycle: ensure all acquired resources are released on every code path.

    Examples (non-exhaustive):
    - Close/cleanup: io.Closer, rows iterators, files, response bodies, sessions.
    - Avoid leaking goroutines by ensuring cancellation/Close is wired through.
  tags:
    - risk:correctness
    - theme:error-handling
    - lang:go
  rationale: Resource leaks commonly hide in error paths and lead to stability issues.

- rule_id: XHY-PRR-002
  description: |
    Concurrency safety: verify shared state access is synchronized and lock ordering is consistent.

    Check:
    - Data race risk (map/slice mutation, counters, cached structs)
    - Lock order and potential deadlocks
    - Context cancellation propagation for long-running work
  tags:
    - risk:concurrency
    - lang:go
  rationale: Subtle concurrency bugs are hard to reproduce and expensive to debug.

- rule_id: XHY-PRR-003
  description: |
    Error handling: avoid swallowing errors, return actionable context, and keep error flows explicit.

    Check:
    - Errors are wrapped with context where useful
    - Non-nil errors are not ignored
    - Partial failure is handled (cleanup + rollback where applicable)
  tags:
    - theme:error-handling
    - risk:correctness
    - lang:go
  rationale: Clear error boundaries prevent silent correctness regressions.

- rule_id: XHY-PRR-004
  description: |
    Security and logging hygiene:
    - Do not log secrets or sensitive identifiers by default.
    - Avoid logging unbounded user input or large payloads.
    - Prefer structured logging and stable error messages.
  tags:
    - risk:security
    - risk:ops
    - theme:api
  rationale: Logging is a common exfiltration and stability risk.

- rule_id: XHY-PRR-005
  description: |
    Compatibility and user-facing contracts:
    - If config/system variables are involved, verify units and default values are consistent
      across docs, parsing, validation, and usage.
    - Confirm backward-compatible behavior for upgrades/rollbacks when semantics change.
  tags:
    - risk:compat
    - scenario:upgrade
    - scenario:rollback
    - theme:api
  rationale: Mismatched units or defaults can silently break production behavior.

- rule_id: XHY-PRR-006
  description: |
    Verification discipline:
    - Prefer targeted tests over broad suites.
    - Include minimal, copy-pastable verification commands in the review when suggesting tests.
    - If the codebase uses special build tags for integration tests, include them when needed.
  tags:
    - theme:testing
    - risk:correctness
  rationale: Reviews become more actionable when verification is reproducible.

- rule_id: XHY-PRR-007
  description: |
    Avoid unnecessary I/O and unbounded reads when a streaming approach is sufficient.
    In particular, avoid patterns equivalent to reading whole bodies into memory without limits
    unless the size is bounded by design.
  tags:
    - risk:perf
    - theme:api
    - lang:go
  rationale: Unbounded reads are both performance and stability risks.

- rule_id: XHY-PRR-008
  description: |
    Test hygiene:
    - If verification requires enabling special test knobs (e.g., failpoints or build tags),
      ensure the review includes explicit enable/disable or cleanup guidance.
  tags:
    - theme:testing
    - risk:ops
  rationale: Reviews should not leave the workspace or environment in a surprising state.
# xuhuaiyu criteria

- rule_id: XUHUAIYU-GO-RESOURCE-001
  description: Ensure all opened resources are closed on every path (e.g., resp.Body, rows, files, iterators), ideally via defer after successful open.
  tags:
    - lang:go
    - risk:correctness
    - risk:ops
    - scope:tidb
  rationale: Resource leaks cause flaky tests, stuck goroutines, and production stability issues.
  examples:
    - "HTTP client response body is not closed"
    - "sql.Rows is not closed"

- rule_id: XUHUAIYU-GO-CONCURRENCY-001
  description: Verify goroutines have a deterministic lifetime and termination path (context cancellation, error propagation, waitgroup usage), and avoid goroutine leaks on early returns.
  tags:
    - lang:go
    - risk:concurrency
    - risk:ops
    - scope:tidb
  rationale: Goroutine leaks are hard to detect and can degrade performance or hang tests.

- rule_id: XUHUAIYU-ERROR-CTX-001
  description: When returning errors from lower layers, wrap or annotate them with enough context (operation, key params) to preserve debugging signal.
  tags:
    - theme:error-handling
    - risk:correctness
    - scope:tidb
  rationale: Context-rich errors reduce MTTR and avoid silent misclassification upstream.

- rule_id: XUHUAIYU-API-COMPAT-001
  description: For any API/contract change (including config or system variable behavior), confirm defaults, units, and accepted ranges are consistent across parsing, docs, and examples.
  tags:
    - theme:api
    - risk:compat
    - scope:tidb
  rationale: Unit/type mismatches can silently break users and create hard-to-debug production incidents.

- rule_id: XUHUAIYU-API-COMPAT-002
  description: Avoid breaking public interfaces or persistent formats unless explicitly versioned; if unavoidable, require a migration note and compatibility tests.
  tags:
    - risk:compat
    - scope:tidb
  rationale: Compatibility breaks are expensive and should be deliberate, documented, and test-covered.

- rule_id: XUHUAIYU-PERF-STREAM-001
  description: Prefer streaming over unbounded reads; avoid io.ReadAll or large in-memory buffers when incremental processing is sufficient.
  tags:
    - risk:perf
    - risk:ops
    - scope:tidb
  rationale: Unbounded reads can cause memory spikes and tail latency regressions.

- rule_id: XUHUAIYU-OBS-LOGGING-001
  description: Ensure logs are actionable and safe: avoid logging unbounded payloads and ensure error logs include context without leaking sensitive data.
  tags:
    - theme:observability
    - risk:ops
    - risk:security
    - scope:tidb
  rationale: Poor logging can cause log flooding, cost spikes, and incident response blind spots.

- rule_id: XUHUAIYU-TEST-FAILPOINT-001
  description: If the change relies on failpoints, ensure tests enable failpoints explicitly and disable them in cleanup, so the workspace and subsequent tests remain unaffected.
  tags:
    - theme:testing
    - risk:correctness
    - risk:ops
    - scope:tidb
  rationale: Leaving failpoints enabled can create non-deterministic failures and hidden coupling between tests.

- rule_id: XUHUAIYU-TEST-TARGETED-001
  description: When behavior changes, require a targeted test that exercises the new behavior and fails under the old behavior; avoid relying on broad integration tests alone.
  tags:
    - theme:testing
    - risk:correctness
    - scope:tidb
  rationale: Targeted tests make regressions obvious and speed up diagnosis.
