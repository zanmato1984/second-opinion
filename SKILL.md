---
name: second-opinion
description: "Reviewer-centric prompt compiler for AI code review in this repository. Use when asked to run or modify the tagger/compiler/reviewer prompts, update reviewer criteria or taxonomy, validate schemas, add golden examples, or package/install the Second Opinion skill."
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
