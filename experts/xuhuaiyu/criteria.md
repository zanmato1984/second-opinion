# Xuhuaiyu expert criteria

- rule_id: XUHUAIYU-PR-001
  description: |
    Check for resource leaks on all error/success paths: missing `Close`/`Flush`,
    goroutine leaks, and unclosed HTTP response bodies (`resp.Body`).
    Ensure cleanup happens even when early returns occur.
  tags:
    - theme:error-handling
    - risk:correctness
    - risk:ops
  rationale: Resource leaks often surface as production instability and hard-to-debug incidents.

- rule_id: XUHUAIYU-PR-002
  description: |
    For concurrency-sensitive changes, validate lock ordering and cancellation:
    avoid deadlocks, data races, and stuck goroutines. Prefer explicit ownership,
    avoid holding locks while performing IO, and ensure contexts are respected.
  tags:
    - risk:concurrency
    - risk:correctness
  rationale: Concurrency bugs are high-impact and typically escape shallow testing.

- rule_id: XUHUAIYU-PR-003
  description: |
    Ensure errors are handled consistently: do not silently ignore errors; return
    or wrap them with enough context. Avoid partial failure states and ensure
    callers can distinguish retryable vs non-retryable errors when applicable.
  tags:
    - theme:error-handling
    - risk:correctness
  rationale: Error handling contracts are part of API behavior and affect reliability.

- rule_id: XUHUAIYU-PR-004
  description: |
    Scan for security footguns: avoid logging secrets/tokens, avoid unbounded
    reads/writes (e.g. `io.ReadAll` on untrusted input), and review defaults for
    unsafe behavior. Prefer least-privilege and explicit limits.
  tags:
    - risk:security
    - risk:ops
  rationale: Small review misses can become security incidents or DoS vectors.

- rule_id: XUHUAIYU-PR-005
  description: |
    When changing configuration, system variables, or user-facing rules, ensure
    contract consistency: units, parsing types, comparison types, and default
    values must align across docs/examples/implementation. Consider upgrade and
    rollback behavior for compatibility risk.
  tags:
    - risk:compat
    - risk:correctness
    - scenario:upgrade
  rationale: Contract drift breaks users silently and is expensive to fix later.

- rule_id: XUHUAIYU-PR-006
  description: |
    Validate the test strategy is fit-for-purpose: add targeted unit/integration
    tests for behavior changes and edge cases. If verification requires enabling
    failpoints, ensure they are disabled afterward to avoid contaminating
    subsequent runs.
  tags:
    - theme:testing
    - risk:correctness
  rationale: Tests are the fastest way to turn review concerns into durable guarantees.
