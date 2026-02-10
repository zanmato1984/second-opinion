# pr-baseline process workflow

- workflow_id: PR-BASELINE-001
  name: Baseline PR review
  body: |
    Goal: provide a lightweight, consistent review baseline.

    Workflow:
    1) Summarize change intent in 1-2 bullets (review.md only).
    2) Check correctness, error handling, and missing tests at a high level.
    3) Emit findings only when you can point to a concrete location in the diff.

    Output format:
    - review.md sections:
      Summary:
      Findings:
    - review.json must follow the repository schema.
      For findings produced from this workflow:
        - source: {type: "process", id: "pr-baseline"}
        - tags: include at least one relevant tag from taxonomy.md
    - If no issues are found, return review.json with an empty findings array.
