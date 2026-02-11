# Second Opinion

Second Opinion is a contributor-driven repository for building a structured
code review skill. The system uses a prompt pipeline (tagger → compiler →
reviewer) and a controlled taxonomy to produce attributable review outputs.

This repo includes sample foo assets in each contributor asset directory to
show formatting and organization; exclude them from real reviews.

## Repository layout

- taxonomy.md: Controlled tag vocabulary used by all prompts.
- prompts/: Tagger, compiler, and reviewer prompt templates.
- schemas/: JSON schemas for structured outputs.
- experts/: Contributor-owned expert criteria (includes sample foo assets).
- processes/: Contributor-owned workflows (includes sample foo assets).
- policies/: Always-on guardrails (includes sample foo assets).
- fragments/: Reusable shared guidance (includes sample foo assets).
- examples/: Golden examples for regression tests (includes sample foo assets).
- skills/: Codex skills for this repo, including contributor tooling.

## How to contribute

The only supported contribution path is the `oh-my-second-opinion` skill.
Run it and follow the prompts. It will:

- Ask for your SKILL.md content and attribution preferences.
- Propose an integration plan for experts, processes, policies, and fragments.
- Explain the plan and ask for confirmation before making edits.

## Adding or updating taxonomy tags

Tags are a controlled vocabulary. Only tags listed in taxonomy.md are allowed.

When you need a new tag:

1) Update taxonomy.md with the new tag(s).
2) Keep tags in English.
3) For component tags, mirror TiDB GitHub labels that use `component/` or
   `sig/` naming as `component:<name>`.
4) Update or add tests that validate the taxonomy change.

## Language policy

All assets and code in this repo must be in English, except for
language-specific templates.
