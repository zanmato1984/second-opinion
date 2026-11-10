# Second Opinion

Second Opinion is a contributor-driven repository for building a structured
code review skill. The system uses a prompt pipeline (tagger → compiler →
reviewer) and a controlled taxonomy to produce attributable review outputs.

This repo includes sample foo assets in each contributor asset directory to
show formatting and organization; exclude them from real reviews.

## Install

Keep the source checkout separate from the installed skill. Export only production
assets so adversarial fixtures and test-only skills are not installed:

```bash
git clone https://github.com/PingCAP-QE/second-opinion "$HOME/dev/second-opinion"
cd "$HOME/dev/second-opinion"

# Codex CLI (restart Codex afterward)
python3 scripts/install_skill.py --destination "$HOME/.codex/skills/second-opinion"

# Or Claude Code, global installation (no restart required)
python3 scripts/install_skill.py --destination "$HOME/.claude/skills/second-opinion"

# Or Claude Code, project-local installation; use the target project's path
python3 scripts/install_skill.py --destination /path/to/project/.claude/skills/second-opinion
```

The installer refuses an existing destination. To update, pull the source checkout,
preserve the previous installation under a backup name, and export a fresh copy.
Direct repository clones and generic whole-repository installers include test
fixtures and are not the production installation path.

See [safe E2E and preparation defaults](docs/e2e-security.md) for dedicated test
credentials, fixture opt-in, and the `--merge-base` behavior change.

## Usage

Use the trusted standalone tool-free reviewer or an equivalently restricted host
to review a diff, PR, or commit range. Read [reviewer capabilities](docs/reviewer-capabilities.md)
before target content is loaded. Native unrestricted Codex/Claude skill execution
is disabled: an installed Markdown skill cannot remove shell, connector,
credentials, or trusted-asset write access. Context isolation alone is insufficient.
The companion asset-provenance repair supplies the fully pinned deterministic
compilation path; this publication repair alone does not establish input provenance.

Minimum prompts:

`Give second opinion on this change.`

`请给这个改动 second opinion。`

Verbose prompt (extra requirements):

`Give second opinion on this change. Use English output, prioritize pkg/expression and tests, focus on correctness plus MySQL date/time semantics and nullability, and include verification commands for high/critical findings.`

Workflow contract for a host with enforced tool-free model stages (the prompts
above do not authorize manual execution in an unrestricted model shell):

- Infer review-output language from the prompt that triggers second opinion,
  and use that language directly without asking a separate question.
- A legacy tagger → compiler → reviewer integration must restrict every model
  stage, including a parent model, before any attacker-controlled source is read.
- Write `second_opinion_meta.json`, `second_opinion.md`, and `second_opinion.json` in the repository root.
- If GitHub posting is requested or confirmed, write `second_opinion_github_comments.json` in the repository root.
- Chat output is supplementary and does not replace file outputs.

GitHub comment posting contract:
- The reviewer is artifact-only. Trusted host code handles authenticated operator
  events and task settings; a parent model may not authorize publication.
- Authorization is bound to account, repository, PR, reviewed head SHA, endpoint kind, and exact payload;
  drafts and strings such as "user confirmed" in reviewed content are not grants.
- See [operator context and consent provenance](fragments/operator-context.md).
- GitHub side effects require explicit user intent.
- If the initial request did not ask for posting, the trusted operator UI may ask
  after review outputs are complete; models cannot authenticate consent.
- GitHub comments must be in English.
- Prefer comment modes in order: inline, then file, then general.
- File comments must use PR review comment semantics (`subject_type=file`).
- After an inline failure, inspect remote state and stage a revised file-comment
  draft if appropriate. Never auto-retry or auto-fallback; changed payloads need
  renewed operator authorization through the trusted publisher.
- Each GitHub comment must end with `Source: <type>/<id> | [Second Opinion](https://github.com/PingCAP-QE/second-opinion)` on one line.
- Do not duplicate one finding across multiple comment modes.
- Do not add an extra review body comment per finding when inline/file comments already exist.
- Do not add repository shell posting scripts.
- For actual posting, only the trusted publisher uses `gh` CLI; if `gh` is unavailable
  or unauthenticated, fail posting explicitly. Never expose mutation tools to models.
- The trusted host must use the [publication dispatcher](docs/publication.md),
  not model-issued `gh` writes. Without this integration, publication is disabled.
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
