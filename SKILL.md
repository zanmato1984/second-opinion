---
name: second-opinion
description: "Consolidated PingCAP reviewer skill for local code review. Trigger when the user asks for a second opinion on a change (e.g., 'give second opinion on this change' or 'do code review for second opinion')."
---

# Second Opinion

## Workflow

- Run the review workflow (tagger → compiler → review) on the provided diff.
- Produce `review.md` and `review.json` output.
