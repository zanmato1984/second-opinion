---
name: second-opinion
description: "Consolidated PingCAP review expert skill for local code review. Trigger when the user asks for a second opinion on a change (e.g., 'give second opinion on this change' or 'do code review for second opinion')."
---

# Second Opinion

## Host capability preflight

Autonomous review requires a host-enforced artifact-only capability boundary.
The reviewing model must not receive GitHub write credentials, shell/network
tools, mutating MCP connectors, or write access to trusted skill assets. The
trusted parent supplies source evidence and writes returned review artifacts.
Use the tool-free reference path in scripts/review_only.py from a trusted source
checkout, or an equivalent restricted host. See docs/reviewer-capabilities.md.
If the host cannot provide this boundary, do not launch an unrestricted reviewer;
report the missing host integration. A prompt rule is not enforcement.

## Asset Location (Claude Code only)

The review assets (taxonomy, experts, processes, policies, fragments, prompts)
live in the skill's installation directory. Determine the base path by checking
these locations in order and using the first one where `taxonomy.md` exists:

1. `~/.claude/skills/second-opinion/` (global install)
2. `.claude/skills/second-opinion/` (project-local install)
3. The current working directory (when invoked inside the repo itself)

Read all referenced assets from that base path throughout this workflow.

## Workflow

- Infer the review-output language from the user prompt that triggers
  second opinion.
- Use the inferred language for user-facing review communication.
- Do not ask a separate language-preference question unless the user asks
  to override the inferred language.
- Ensure all assets and code in this repo are in English, except for
  language-specific templates.
- If a subagent is available for the review stage, use it only when it
  provides context isolation; otherwise explicitly instruct it to ignore
  prior context and use only compiled_prompt + diff.
- Ignore sample foo assets under experts/foo, processes/foo, policies/foo.yaml,
  fragments/foo.md, and examples/foo; they are format references only.
- Run the review workflow (tagger → compiler → review) on the provided diff.
- The compiler deterministically selects processes and experts, and always includes policies.
- Write artifacts to the workspace root:
  - emit `second_opinion_meta.json` with selection rationale after the compiler stage
  - produce `second_opinion.md` and `second_opinion.json` after the review stage
- If GitHub posting is requested or confirmed, also produce `second_opinion_github_comments.json` in the workspace root.
- If posting was not requested initially, ask whether to post only after review outputs are complete.
- GitHub comment posting must use English, prefer inline/file comments over general comments,
  and end comments with `Source: <type>/<id> | [Second Opinion](https://github.com/PingCAP-QE/second-opinion)`.
- File comments must use PR review comment semantics (`subject_type=file`), and inline failures due to unresolved lines should retry as file comments.
- Do not duplicate one finding across multiple comment modes, and do not add an extra review body comment per finding when inline/file comments are posted.
- For actual posting, use `gh` CLI; if `gh` is unavailable or unauthenticated, fail posting explicitly.
- Chat findings are supplementary; they do not replace required file outputs.
