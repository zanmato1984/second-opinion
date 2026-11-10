# Remote branch review workflow (upstream-aligned)

## 0) Language and Inputs

Apply shared language contract from `fragments/review-language-contract.md`.

Accept either:
- `<pr_url>`
- `<review_remote_url> <review_branch>`

Optional flags:
- `--base <master|main|custom>`
- `--paths p1,p2,...`
- `--no-merge-base`
- `--merge-base` (explicit local base merge)
- `--run-tests`

## 1) Baseline preparation

- Ensure `upstream` exists and fetch the latest base branch (`master`, fallback `main`).
- Fetch the target review branch from a deterministic review remote.
- Create a codex-owned local review branch under `codex/review/*`.
- Use a fresh isolated worktree; never overwrite an existing review branch or worktree.
- Keep the fetched review head unchanged by default. Locally merge the latest upstream
  base only when the user explicitly requests `--merge-base`.

Helper:
- Use `processes/review-branch/prepare_review.sh` for repeatable setup.

## 2) Scope and evidence

- Compute review scope from `BASE...HEAD` after baseline alignment.
- Prefer user-provided artifacts and path-focused reading when `--paths` is set.
- For uncertain logic, follow call chains until invariants and side effects are clear.

## 3) Review dimensions

Always check:
- correctness and error handling
- concurrency and resource lifecycle
- security footguns and unsafe defaults

Conditionally check:
- compatibility/upgrade impacts when behavior or public contracts change
- hot-path performance when modified code is execution-critical

## 4) Output contract

Produce both:
- `second_opinion.md`: summary + guided reading path + prioritized findings
- `second_opinion.json`: schema-compliant findings with source attribution and severity

Write these files in the repository root. Printed chat findings do not satisfy
this output contract.

Testing note:
- CI is authoritative by default; only run local tests when explicitly requested.

If GitHub posting is requested or confirmed, also prepare:
- `second_opinion_github_comments.json`: comment payload draft following `fragments/github-comment-contract.md`.

## 5) Posting decision gate

Sections 5 and 6 are trusted-host-only, never model instructions. The reviewer
returns artifact data and optional drafts; it never authenticates consent or runs
GitHub writes. Trusted host code follows `fragments/operator-context.md` to bind
real operator authorization to the account, repository, PR, reviewed head SHA,
endpoint kind, and complete payload. An unrestricted parent model is unsupported.

After writing `second_opinion.md` and `second_opinion.json`:
- If the initial user request explicitly asked for GitHub posting, trusted host
  code may dispatch the exact authorized payload through the publisher.
- Otherwise the trusted operator UI may ask whether the user wants posting and
  wait for explicit confirmation; models cannot authenticate this event.
- Posting GitHub review comments requires PR context (`<pr_url>` input mode).
- If the review runs in `<review_remote_url> <review_branch>` mode without a PR URL, fail posting explicitly and keep local outputs only.

## 6) Side-effect boundary

Never perform GitHub operations with side effects unless explicitly requested.
Do not add repository shell posting scripts for GitHub comments.
For actual posting, only the trusted publisher uses `gh` CLI. No model stage
may invoke mutating `gh` commands or supply its own approval through a shell/PTY.
The trusted host must use `runtime/github_publisher.py` or the operator-terminal
`scripts/publish_review.py`; raw model-issued `gh` writes are not supported.
If this integration is absent, retain local outputs and fail publication closed.
If `gh` is unavailable or unauthenticated, fail the posting step explicitly and stop.

A failed write must not auto-retry or auto-fallback. Inspect remote state before
staging a changed payload, then obtain renewed authorization outside all models.
