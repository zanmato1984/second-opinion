# Second Opinion

Second Opinion is a contributor-driven repository for building a structured
code review skill. The system uses a prompt pipeline (tagger → compiler →
reviewer) and a controlled taxonomy to produce attributable review outputs.

This repo includes sample foo assets in each contributor asset directory to
show formatting and organization; exclude them from real reviews.

## Install

### Codex CLI

From the Codex CLI prompt, run:

```bash
$skill-installer https://github.com/PingCAP-QE/second-opinion
```

Restart Codex after installation to load the skill.

### Claude Code

Clone the repository into your Claude skills directory:

```bash
# Global install (available in all projects)
git clone https://github.com/PingCAP-QE/second-opinion ~/.claude/skills/second-opinion

# Or project-local install
git clone https://github.com/PingCAP-QE/second-opinion .claude/skills/second-opinion
```

No restart required. The skill is immediately available as `/second-opinion` or
triggered automatically when you ask for a code review second opinion.

To update later:

```bash
git -C ~/.claude/skills/second-opinion pull
```

## Usage

Use `second-opinion` to review a diff, PR, or commit range.

Minimum prompts:

`Give second opinion on this change.`

`请给这个改动 second opinion。`

Verbose prompt (extra requirements):

`Give second opinion on this change. Use English output, prioritize pkg/expression and tests, focus on correctness plus MySQL date/time semantics and nullability, and include verification commands for high/critical findings.`

Workflow contract (applies even with the minimum prompt):

- Infer review-output language from the prompt that triggers second opinion,
  and use that language directly without asking a separate question.
- Run tagger → compiler → reviewer.
- Write `second_opinion_meta.json`, `second_opinion.md`, and `second_opinion.json` in the repository root.
- If GitHub posting is requested or confirmed, write `second_opinion_github_comments.json` in the repository root.
- Chat output is supplementary and does not replace file outputs.

GitHub comment posting contract:
- GitHub side effects require explicit user intent.
- If the initial request did not ask for posting, ask after review outputs are complete.
- GitHub comments must be in English.
- Prefer comment modes in order: inline, then file, then general.
- File comments must use PR review comment semantics (`subject_type=file`).
- If inline posting fails due to unresolved line context, retry as file comment before general comment.
- Each GitHub comment must end with `Source: <type>/<id> | [Second Opinion](https://github.com/PingCAP-QE/second-opinion)` on one line.
- Do not duplicate one finding across multiple comment modes.
- Do not add an extra review body comment per finding when inline/file comments already exist.
- Do not add repository shell posting scripts.
- For actual posting, use `gh` CLI; if `gh` is unavailable or unauthenticated, fail posting explicitly.
- Posting review comments requires PR URL context; bare branch review mode is local-output-only.

## Repository layout

For a host-enforced, tool-free review path and its integration requirements, see
[reviewer capabilities](docs/reviewer-capabilities.md). A skill's prompt policy
alone does not revoke the host's tools or credentials.

- SKILL.md: Skill definition (compatible with both Codex CLI and Claude Code).
- taxonomy.md: Controlled tag vocabulary used by all prompts.
- prompts/: Tagger, compiler, and reviewer prompt templates.
- schemas/: JSON schemas for structured outputs.
- experts/: Contributor-owned expert criteria (includes sample foo assets).
- processes/: Contributor-owned workflows (includes sample foo assets).
- policies/: Always-on guardrails (includes sample foo assets).
- fragments/: Reusable shared guidance (includes sample foo assets).
- examples/: Golden examples for regression tests (includes sample foo assets).
- skills/: Sub-skills for this repo, including contributor tooling.

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
3) For component tags, include the repo name as `component:<repo>/<name>`
   (for example, `component:tidb/ddl`) and mirror labels that use
   `component/` or `sig/` naming.
4) Update or add tests that validate the taxonomy change.

## Language policy

All assets and code in this repo must be in English, except for
language-specific templates.
