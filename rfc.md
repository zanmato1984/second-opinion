# RFC: Second Opinion — Consolidated PingCAP Reviewer Skill

## Status

Draft

## Authors

Rossi Sun, contributors

---

## Overview

This document defines Second Opinion, a consolidated PingCAP expert review skill
for local code review. The skill packages expert criteria, taxonomy, prompts,
schemas, and tests into a single installable artifact while using a
structured review pipeline to produce attributable review outputs.

The system is designed to:

- Ship as one installable skill with all artifacts included
- Preserve strong contributor identity and credit
- Avoid monolithic prompts
- Enable explainable expert selection
- Provide deterministic workflow selection with a rationale trail
- Support deterministic guardrails inside a prompt-only workflow
- Integrate easily with agentic coding tools such as Codex CLI and Claude Code CLI
- Remain portable across environments

---

## Goals

- Encode senior engineers’ review heuristics in reusable form
- Select experts dynamically based on code changes
- Compile a tailored review prompt for each change
- Attribute findings back to specific experts and rules
- Record a deterministic workflow selection rationale
- Provide telemetry for overall skill adoption and per-rule adoption
- Keep the system prompt-first and tool-light
- Support regression testing through prompt artifacts
- Control prompt growth through tagging and budgeting

---

## Non-Goals

- Replacing human reviewers
- Building a full IDE
- Implementing static analysis engines
- Hard-coding expert selection logic in code
- Binding to a single LLM provider

---

## Conceptual Model

The system operates as a Prompt Compiler Pipeline.

Given a diff and repository context:

1. Detect signals and derive tags
2. Match tags to experts
3. Select applicable rules from experts’ criteria
4. Deduplicate and order rules
5. Assemble a final review prompt
6. Execute a single review pass
7. Produce structured, attributable output

All stages communicate through structured prompt outputs.

---

## Expert Organization

Each expert corresponds to a real engineer or expertise area.

Repository structure:

experts/
  alice/
    criteria.md
    meta.yaml
  bob/
    criteria.md
    meta.yaml
processes/
  re2/
    criteria.md
    meta.yaml

Each expert owns:

- Their criteria rules
- Preferred tags
- Excluded tags
- Review scope
- Participation limits

---

## Expert Kinds

The system supports multiple expert kinds:

- person — real engineers encoding their heuristics
- domain — subject-matter expertise (e.g., concurrency, performance)
- component — subsystem focus (e.g., TiKV, DDL)

Process workflows are first-class entries under processes/ and are selected via activation metadata plus priority/cost signals.

---

## Reviewer Criteria Format

Expert knowledge is expressed as atomic rules.

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

## Process Workflow Model

Process workflows define structured, multi-step review workflows.

They are activated conditionally based on tags and signals.

Process workflow metadata template:

id: re2
kind: process
owner: alice
description: Invariant-first adversarial deep review workflow
priority: 50
cost: heavy
mode: exclusive
default: false
activation:
  required_tags:
    - risk:concurrency
    - risk:correctness
  any_tags: []
  min_files: 3
  scopes: [scope:tidb]
  langs: [lang:go]

Field semantics:

- priority: higher wins in primary selection (default 0).
- cost: light | medium | heavy (default medium), used for budget.
- mode: exclusive | stackable (default exclusive).
- default: fallback when no candidates match (default false).
- activation.required_tags: all must be present.
- activation.any_tags: at least one must be present (optional).
- activation.min_files: minimum changed files.
- activation.scopes/langs: constrain by tags if present.

When selected:

- The entire workflow block is injected into the compiled prompt
- Steps must be executed in order
- Output must reference workflow stages
- Process workflows are attributed separately from experts

---

## Shared Blocks

Fragments are reusable content pieces (evidence, checklists, output contracts)
that can be referenced by processes or inserted during compilation. They are not
attributed to a specific expert and live under fragments/.

---

## Policies

Policies are organization-wide guardrails that are always included in the
compiled prompt. They live under policies/ and are ordered by priority.

---

## Workflow Selection Algorithm

Selection is deterministic and recorded in the compiler output.

1. User override: if the user names a workflow, select it exclusively unless they request multiple.
2. Candidate filter: keep only processes whose activation rules match tags and diff metadata.
3. Default fallback: if no candidates match, select the first process with default: true.
4. Primary selection: choose the candidate with highest priority.
5. Tie-breakers: prefer higher specificity (more activation constraints), then lower cost.
6. Optional secondary: if primary is stackable, add additional candidates only if within budget.
7. Emit selection_rationale with candidates, primary, secondary, and tie-break details.

If no candidates and no default exist, process selection is empty and recorded as such.

At least one lightweight process should be marked default: true (e.g., pr-baseline)
to provide a baseline workflow when no specialized process matches.

Policies are always selected and included in a fixed priority order.

---

## Compilation Order

The compiler assembles the final prompt in this order:

1. Policies (fixed priority order)
2. Primary process workflow
3. Secondary process workflow (optional)
4. Reviewer rules (atomic checks)
5. Output contract fragment (from fragments/output-*.md)

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
- expert metadata (experts/*)
- process metadata (processes/*)
- policy metadata (policies/*)
- shared fragments (fragments/*)
- expert criteria

Responsibilities:

- Match tags to experts
- Select relevant atomic rules
- Deduplicate overlapping rules
- Select process workflows using the deterministic algorithm
- Insert full process workflows when triggered
- Insert policy requirements (always)
- Assemble the final review instructions
- Preserve provenance for every rule and workflow
- Emit selection rationale for process workflows

Output JSON:

{
  "selected_experts": ["alice"],
  "rules_used": {
    "alice": ["ALICE-CONCURRENCY-001"]
  },
  "selected_processes": ["re2"],
  "selected_policies": ["security", "compat"],
  "selection_rationale": {
    "user_override": null,
    "candidates": [
      {"process": "re2", "reason": "required_tags matched; min_files met"}
    ],
    "primary_process": {"process": "re2", "reason": "highest priority"},
    "secondary_processes": [],
    "tie_breakers": ["specificity", "cost"],
    "budget": "medium"
  },
  "compiled_prompt": "...",
  "provenance": [
    {"rule_id": "ALICE-CONCURRENCY-001", "expert": "alice"},
    {"process": "re2", "triggered_by": ["risk:correctness"]},
    {"policy": "security", "reason": "always"},
    {"policy": "compat", "reason": "always"}
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
- source (type + id)
- tags
- severity
- message

---

## Attribution Model

Contribution is derived from:

- Which rules produced findings
- Which experts authored those rules
- Which tags caused selection
- Which process workflows were triggered
- Which workflow selection rationale led to those triggers
- Which policies were included

No subjective scoring without references.

---

## Prompt-Only Guardrails

To maintain stability:

- Temperature set to zero for selection and compilation
- Strict JSON schemas for all stages
- Maximum experts per run
- Maximum atomic rules per expert
- Mandatory provenance fragments
- Mandatory workflow selection rationale
- Rules must be inserted verbatim
- Process workflows cannot be partially injected
- Only selection, ordering, and deduplication allowed

---

## Repository Artifacts

Minimal structure:

RFC.md
taxonomy.md
experts/
  alice/criteria.md
processes/
  re2/criteria.md
  pr-baseline/criteria.md
fragments/
  evidence.md
  checklists.md
  output-cn.md
  output-en.md
  risk-matrix.md
policies/
  security.yaml
  compat.yaml
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
- Expected expert selections
- Required rule hits
- Required process workflow triggers
- Required workflow selection rationale fields
- Drift measurements across repeated runs
- Manual or scripted replays
 - Test-only fixtures live under tests/fixtures and are ignored by default.

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

- Expert selection drift
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

- Five experts
- Thirty rules each
- Twenty golden diffs

### Phase 2

- Expert packs
- Attribution dashboards
- Tag coverage metrics
- Telemetry usage function to record overall skill adoption and individual rule adoption

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

Second Opinion is a consolidated PingCAP expert review skill that bundles taxonomy,
expert criteria, prompts, schemas, and tests into a single installable package,
running a structured review pipeline to produce attributable, structured code
review output.
