# Output contract: review.md and review.json

Produce two outputs:
- `review.md`: a readable summary for humans.
- `review.json`: a machine-readable findings list.

`review.json` must be a JSON object with a single top-level field:
- `findings`: an array of findings.

Each finding MUST include:
- `file`: string, file path.
- `lines`: string, use a best-effort range like `L10-L25` or `L42`.
- `source`: object with `type` + `id`.
  - `type` must be one of: `rule`, `process`, `policy`.
  - `id` is the originating rule_id / process id / policy id.
- `tags`: array of taxonomy tags (use only tags defined in `taxonomy.md`).
- `severity`: one of `low`, `medium`, `high`, `critical`.
- `message`: a concise, actionable description + fix direction.

Severity guidance (map "must fix" to severity):
- "Must fix: Yes" → `high` or `critical`
- "Must fix: No" → `low` or `medium`
