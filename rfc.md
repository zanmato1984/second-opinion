# RFC: Second Opinion — Consolidated PingCAP Reviewer Skill

## Status

Draft

## Authors

Rossi Sun, contributors

---

## Overview

This document defines Second Opinion, a consolidated PingCAP reviewer skill for
local code review. The skill packages reviewer criteria, taxonomy, prompts,
schemas, and tests into a single installable artifact while using a
reviewer-centric prompt pipeline to produce attributable review outputs.

The system is designed to:

- Ship as one installable skill with all artifacts included
- Preserve strong contributor identity and credit
- Avoid monolithic prompts
- Enable explainable reviewer selection
- Support deterministic guardrails inside a prompt-only workflow
- Integrate easily with agentic coding tools such as Codex CLI and Claude Code CLI
- Remain portable across environments

---

## Goals

- Encode senior engineers’ review heuristics in reusable form
- Select reviewers dynamically based on code changes
- Compile a tailored review prompt for each change
- Attribute findings back to specific reviewers and rules
- Keep the system prompt-first and tool-light
- Support regression testing through prompt artifacts
- Control prompt growth through tagging and budgeting

---

## Non-Goals

- Replacing human reviewers
- Building a full IDE
- Implementing static analysis engines
- Hard-coding reviewer selection logic in code
- Binding to a single LLM provider

---

## Conceptual Model

The system operates as a Prompt Compiler Pipeline.

Given a diff and repository context:

1. Detect signals and derive tags
2. Match tags to reviewers
3. Select applicable rules from reviewers’ criteria
4. Deduplicate and order rules
5. Assemble a final review prompt
6. Execute a single review pass
7. Produce structured, attributable output

All stages communicate through structured prompt outputs.

---

## Reviewer-Centric Organization

Each reviewer corresponds to a real engineer.

Repository structure:

reviewers/
  alice/
    criteria.md
    meta.yaml
  bob/
    criteria.md
    meta.yaml

Each reviewer owns:

- Their criteria rules
- Preferred tags
- Excluded tags
- Review scope
- Participation limits

---

## Reviewer Kinds

The system supports multiple reviewer kinds:

- person — real engineers encoding their heuristics
- domain — subject-matter expertise (e.g., concurrency, performance)
- component — subsystem focus (e.g., TiKV, DDL)
- process — full end-to-end review workflows and methodologies

Process reviewers represent strict review philosophies or deep audit workflows rather than individual risk areas.

---

## Reviewer Criteria Format

Reviewer knowledge is expressed as atomic rules or workflows.

Each rule contains:

- rule_id
- description
- tags
- rationale
- examples (optional)

Example:

- rule_id: ALICE-CONCURRENCY-001
  description: Ensure map mutations in Go are guarded by mutexes.
  tags:
    - lang:go
    - risk:concurrency
    - scope:tidb
  rationale: Production incidents caused by unsafe map writes.

Rules are immutable during compilation.

---

## Process-Style Reviewer Model

Process reviewers define structured, multi-step review workflows.

They are activated conditionally based on tags and signals.

Process reviewer metadata:

id: re2
kind: process
owner: alice
description: Invariant-first adversarial deep review workflow
preferred_tags:
  - risk:correctness
  - scenario:upgrade
activation:
  min_tags:
    - risk:concurrency
    - risk:correctness
  min_files: 3

When selected:

- The entire workflow block is injected into the compiled prompt
- Steps must be executed in order
- Output must reference workflow stages
- Process reviewers are attributed separately from atomic-rule reviewers

---

## Tag Taxonomy

Tags form the primary indexing mechanism.

Only tags from the controlled vocabulary may be used.

### Dimensions

- lang: go | cpp | rust | sql
- scope: tidb | tikv | tiflash | tools
- risk: correctness | concurrency | perf | security | compat | ops
- theme: api | error-handling | testing | build | observability
- scenario: upgrade | rollback | cloud | multi-tenant

New tags require taxonomy updates.

---

## Prompt Pipeline

The system uses three main prompts.

---

### Stage 1 — Tagger Prompt

Input:

- diff
- changed file paths
- repository metadata

Output JSON:

{
  "signals": [
    {"evidence": "pkg/ddl/ddl.go", "reason": "DDL path"},
    {"evidence": "sync.Mutex", "reason": "locking primitive"}
  ],
  "tags": [
    {"tag": "scope:tidb", "why": "ddl path"},
    {"tag": "risk:concurrency", "why": "mutex usage"}
  ]
}

---

### Stage 2 — Compiler Prompt

Input:

- derived tags
- reviewer metadata
- reviewer criteria

Responsibilities:

- Match tags to reviewers
- Select relevant atomic rules
- Deduplicate overlapping rules
- Insert full process workflows when triggered
- Assemble the final review instructions
- Preserve provenance for every rule and workflow

Output JSON:

{
  "selected_reviewers": ["alice", "re2"],
  "rules_used": {
    "alice": ["ALICE-CONCURRENCY-001"]
  },
  "process_reviewers": ["re2"],
  "compiled_prompt": "...",
  "provenance": [
    {"rule_id": "ALICE-CONCURRENCY-001", "reviewer": "alice"},
    {"process": "re2", "triggered_by": ["risk:correctness"]}
  ]
}

---

### Stage 3 — Review Prompt

Input:

- compiled_prompt
- diff

Output:

- review.md
- review.json

Each finding must include:

- file
- lines
- rule_id or workflow_stage
- reviewer
- tags
- severity
- message

---

## Attribution Model

Contribution is derived from:

- Which rules produced findings
- Which reviewers authored those rules
- Which tags caused selection
- Which process workflows were triggered

No subjective scoring without references.

---

## Prompt-Only Guardrails

To maintain stability:

- Temperature set to zero for selection and compilation
- Strict JSON schemas for all stages
- Maximum reviewers per run
- Maximum atomic rules per reviewer
- Mandatory provenance blocks
- Rules must be inserted verbatim
- Process workflows cannot be partially injected
- Only selection, ordering, and deduplication allowed

---

## Repository Artifacts

Minimal structure:

RFC.md
taxonomy.md
reviewers/
  alice/criteria.md
  re2/criteria.md
prompts/
  tagger.prompt
  compiler.prompt
  reviewer.prompt
schemas/
  selection.schema.json
  compile.schema.json
  review.schema.json
examples/

---

## Testing Strategy

Even in a prompt-only system, regression is required.

- Golden diffs stored in examples/
- Expected tag outputs
- Expected reviewer selections
- Required rule hits
- Required process reviewer triggers
- Drift measurements across repeated runs
- Manual or scripted replays

---

## Advantages

- Minimal engineering overhead
- Strong contributor identity
- High portability
- Transparent reasoning chain
- Modular prompt evolution
- Easy integration into agentic tools

---

## Risks

- Reviewer selection drift
- Token explosion
- Semantic rewriting of rules
- Attribution gaming
- Scaling limits

---

## Mitigations

- Tight tag governance
- Atomic rules
- Prompt budget caps
- Provenance enforcement
- Reviewer participation thresholds
- Fast vs deep modes

---

## Phased Rollout

### Phase 1

- Five reviewers
- Thirty rules each
- Twenty golden diffs

### Phase 2

- Reviewer packs
- Attribution dashboards
- Tag coverage metrics

### Phase 3

- CI gating
- Release checks
- Promotion and demotion workflows

---

## Open Questions

- Rule lifecycle management
- Reviewer conflict resolution
- Taxonomy evolution process
- Adversarial prompt resistance
- Long-term scalability

---

## Summary

Second Opinion is a consolidated PingCAP reviewer skill that bundles taxonomy,
reviewer criteria, prompts, schemas, and tests into a single installable package,
running a reviewer-centric prompt pipeline to produce attributable, structured
code review output.
