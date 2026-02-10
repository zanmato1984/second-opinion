---
name: second-opinion
description: "Consolidated PingCAP review expert skill for local code review. Trigger when the user asks for a second opinion on a change (e.g., 'give second opinion on this change' or 'do code review for second opinion')."
---

# Second Opinion

## Workflow

- Run the review workflow (tagger → compiler → review) on the provided diff.
- The compiler deterministically selects processes and experts, and always includes policies.
- Emit `compiler.json` with selection rationale, then produce `review.md` and `review.json`.
