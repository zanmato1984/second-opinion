# Incremental review scope control

Classify the current round as one of:
- First review: no prior baseline in this session.
- Incremental review: new commits exist since the last reviewed baseline.
- Targeted verification: verify specific previously raised items only.

Defaulting rules:
- If there is no prior baseline (no previously reviewed commit/hash in this session), treat it as **first review**.
- Otherwise, treat it as **incremental review**:
  - Focus on the diff since the last reviewed baseline.
  - Re-check previously reported issues only if they are touched by new changes.

For incremental reviews, explicitly separate:
- Whether each previously reported issue is fixed correctly.
- Any remaining non-blocking improvements (only if the new diff touches the area).
