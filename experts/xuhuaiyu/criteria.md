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
