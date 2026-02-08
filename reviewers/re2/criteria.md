# re2 process workflow

- workflow_id: RE2-WORKFLOW-001
  name: Invariant-first adversarial deep review
  steps:
    - stage: invariants
      description: List key invariants touched by the change.
    - stage: diff-audit
      description: Trace each invariant to specific lines in the diff.
    - stage: failure-modes
      description: Enumerate edge cases and adversarial scenarios.
    - stage: tests
      description: Identify missing or weak tests for those scenarios.
