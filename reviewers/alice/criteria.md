# alice criteria

- rule_id: ALICE-CONCURRENCY-001
  description: Ensure map mutations in Go are guarded by mutexes.
  tags:
    - lang:go
    - risk:concurrency
    - scope:tidb
  rationale: Production incidents caused by unsafe map writes.
  examples:
    - "map writes in multiple goroutines without locks"

- rule_id: ALICE-ERROR-001
  description: Check errors from storage operations are wrapped with context.
  tags:
    - theme:error-handling
    - scope:tidb
  rationale: Preserves debugging signal when failures propagate.
