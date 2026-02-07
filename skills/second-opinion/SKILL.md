---
name: second-opinion
description: "Composable AI code review workflow for the Second Opinion repository. Use when asked to run the Second Opinion review pipeline on a unified diff, add or update reviewers/collections, validate output schema, or extend the golden PR regression tests."
---

# Second Opinion

## Overview

Run the local Second Opinion pipeline against diffs, manage reviewer metadata, and keep tests and schema in sync.

## Quick Start (Run a Review)

- Run the CLI on a diff file:

```
conda run -n base python -m adapters.cli --repo pingcap/tidb --diff path/to/patch.diff
```

- Add a collection (bundle of reviewers):

```
conda run -n base python -m adapters.cli --repo pingcap/tidb --diff path/to/patch.diff --collections tidb-core-pack
```

- Limit global prompt budget:

```
conda run -n base python -m adapters.cli --repo pingcap/tidb --diff path/to/patch.diff --max-tokens 2000
```

## Add or Update a Reviewer

- Create a new reviewer folder under `reviewers/<reviewer-id>/`.
- Add `reviewer.yaml` with `id`, `type`, `owners`, `display_name`, `description`, `scopes`, `tags`, `budget`, `rules`.
- Add `prompt.md` and `rules.md`.
- Keep regex patterns YAML-safe (single quotes for backslashes).
- Add or update tests under `tests/` or `tests/golden_prs/`.

## Add or Update a Collection

- Create or edit `collections/<collection-id>.yaml` with a list of reviewer IDs.
- Keep `preferred_types` ordered by priority if needed.

## Validate and Test

- Run the test suite:

```
conda run -n base python -m pytest -q
```

- Ensure JSON schema stays aligned with `schema/review_output.schema.json`.

## Output Contract

- Findings must match the schema fields: `reviewer`, `rule_id`, `file`, `line_range`, `severity`, `message`, `suggestion`, `confidence`.
- Use `schema/review_output.schema.json` as the source of truth.
