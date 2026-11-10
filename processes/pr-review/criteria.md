# PR review workflow (baseline)

## 0) Language

Apply shared language contract from `fragments/review-language-contract.md`.

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
- `second_opinion.md`: a human-readable summary + prioritized list of issues.
- `second_opinion.json`: findings following the repo schema.

Write these files in the repository root. Printed chat findings do not satisfy
this output contract.

For each issue, include:
- what is wrong (one sentence),
- the concrete fix direction,
- how to verify (minimal reproducible commands when possible),
- and map "must fix" to severity (`high`/`critical` vs `low`/`medium`).

If GitHub posting is requested or confirmed, also prepare:
- `second_opinion_github_comments.json`: comment payload draft following `fragments/github-comment-contract.md`.

## 5) Posting decision gate

Sections 5 and 6 are trusted-host-only, never model instructions. The reviewer
returns artifact data and optional drafts; it never authenticates consent or runs
GitHub writes. Trusted host code follows `fragments/operator-context.md` to bind
real operator authorization to the account, repository, PR, reviewed head SHA,
endpoint kind, and complete payload. An unrestricted parent model is unsupported.

After producing `second_opinion.md` and `second_opinion.json`:
- If the initial user request explicitly asked for GitHub posting, trusted host
  code may dispatch the exact authorized payload through the publisher.
- Otherwise the trusted operator UI may ask whether the user wants posting and
  wait for explicit confirmation; models cannot authenticate this event.

## 6) Side-effect boundary

Do not perform any GitHub operation with side effects unless explicitly instructed.
Do not add repository shell posting scripts for GitHub comments.
For actual posting, only the trusted publisher uses `gh` CLI. No model stage
may invoke mutating `gh` commands or supply its own approval through a shell/PTY.
The trusted host must use `runtime/github_publisher.py` or the operator-terminal
`scripts/publish_review.py`; raw model-issued `gh` writes are not supported.
If this integration is absent, retain local outputs and fail publication closed.
If `gh` is unavailable or unauthenticated, fail the posting step explicitly and stop.

A failed write must not auto-retry or auto-fallback. Inspect remote state before
staging a changed payload, then obtain renewed authorization outside all models.
