---
name: second-opinion
description: "Consolidated PingCAP review expert skill for local code review. Trigger when the user asks for a second opinion on a change (e.g., 'give second opinion on this change' or 'do code review for second opinion')."
---

# Second Opinion

## Workflow

- Ask the user about their language usage promptly and make sure all the
  following interaction uses this language.
- Ensure all assets and code in this repo are in English, except for
  language-specific templates.
- If a subagent is available for the review stage, use it only when it
  provides context isolation; otherwise explicitly instruct it to ignore
  prior context and use only compiled_prompt + diff.
- Ignore sample foo assets under experts/foo, processes/foo, policies/foo.yaml,
  fragments/foo.md, and examples/foo; they are format references only.
- Run the review workflow (tagger → compiler → review) on the provided diff.
- The compiler deterministically selects processes and experts, and always includes policies.
- Emit `compiler.json` with selection rationale, then produce `review.md` and `review.json`.
