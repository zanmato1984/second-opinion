# PR review workflow (baseline)

## 0) Language

Ask the user which language they want for the review output, then use it for `review.md`.
All repository assets remain in English.

## 1) Define scope for this round

Classify the round as one of:
- First review: no prior baseline in this session.
- Incremental review: new commits exist since the last reviewed baseline.
- Targeted verification: verify specific previously raised items only.

Default:
- If there is no prior baseline, treat it as **first review**.
- Otherwise treat it as **incremental review** and focus only on the diff since the baseline.

## 2) Collect minimal but sufficient evidence

- Prefer using user-provided artifacts (PR description, changed-files list, diffs) when available.
- For incremental reviews, restrict reading to:
  - the new diff since baseline
  - the touched files only
- Run targeted compilation/tests when feasible; avoid broad test runs unless requested.
- If a test in the target repository requires `--tags=intest`, use it.
- If verification requires enabling failpoints, ensure they are disabled afterward.

## 3) Review dimensions

Always check:
- Correctness: logic bugs, missing error handling, signature/contract mismatches, missing Close/Flush.
- Engineering risk: resource leaks (memory/goroutine/FD/connection/`resp.Body`), concurrency safety, unsafe defaults.
- Security: secret logging, unbounded reads/writes, unsafe IO/network behavior.

Conditionally check (when behavior/contract changes):
- Compatibility and boundaries: defaults, system variables/config, filesystem/object-store paths, HTTP behavior, upgrade/rollback impact.

Optional (non-blocking unless user requests):
- Performance: avoid unnecessary allocations/copies; avoid `io.ReadAll` when streaming is sufficient; avoid extra IO.

## 4) Produce review results

Write:
- `review.md`: a human-readable summary + prioritized list of issues.
- `review.json`: findings following the repo schema.

For each issue, include:
- what is wrong (one sentence),
- the concrete fix direction,
- how to verify (minimal reproducible commands when possible),
- and map "must fix" to severity (`high`/`critical` vs `low`/`medium`).

## 5) Stop and wait

After producing `review.md` and `review.json`, stop and wait for explicit user instruction.
Do not perform any GitHub operation with side effects unless explicitly instructed.
