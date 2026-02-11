# Output contract (review.md + review.json)

This repository produces two outputs:

## review.md

- Human-readable review summary and findings.
- Use the user's preferred language unless otherwise specified.
- Each finding should include:
  - Location (file + approximate lines / hunk context)
  - Severity (low / medium / high / critical)
  - Problem statement
  - Suggested fix direction
  - How to verify (minimal commands or steps)

## review.json

- Must be a single JSON object matching `schemas/review.schema.json`.
- `findings` is an array; each finding must include:
  - `file`: string
  - `lines`: string (free-form; can be a range like "L10-L25" or a hunk reference)
  - `source`: `{ "type": "rule"|"process"|"policy", "id": "<id>" }`
  - `tags`: array of strings (use taxonomy tags where applicable)
  - `severity`: "low" | "medium" | "high" | "critical"
  - `message`: string (can match review.md language)

Severity guidance:
- critical/high: correctness or security issues likely to cause real incidents.
- medium: meaningful risk or maintainability issue.
- low: minor issues, nits, or optional suggestions.
