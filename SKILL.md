---
name: second-opinion
description: "Consolidated PingCAP reviewer skill for local code review. Trigger when the user asks for a second opinion on a change (e.g., 'give second opinion on this change' or 'do code review for second opinion') or asks to update taxonomy, reviewers, prompts, schemas, tests, or installation."
---

# Second Opinion

## Workflow

- This skill is self-contained: all artifacts (taxonomy, prompts, schemas,
  reviewers, examples, tests) live under this directory.
- Read `taxonomy.md` to choose tags; only use listed tags.
- Update reviewer criteria in `reviewers/<id>/criteria.md` and metadata in `reviewers/<id>/meta.yaml`.
- Edit prompt templates in `prompts/*.prompt` and keep outputs aligned with `schemas/*.schema.json`.
- When adding or changing output fields, update schemas and related tests.

## Golden examples

- Create `examples/<case>/patch.diff`.
- Add expected outputs: `tagger.json`, `compiler.json`, `review.json`, and optional `review.md`.
- Ensure expected JSON conforms to the schemas.

## Validation

- Run `python3 -m unittest discover -s tests`.

## Install the skill

- Copy `skills/second-opinion` into `$CODEX_HOME/skills/second-opinion`, or use the skill-installer skill.
