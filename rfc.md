# RFC: Second Opinion — A Composable AI Code Review Skill for Agentic Development

## Status

Draft

## Authors

Rossi Sun, contributors

---

## Summary

Second Opinion is a portable AI-powered code review skill designed to integrate into mainstream agentic coding environments.

Rather than relying on a single monolithic prompt, Second Opinion composes multiple specialized virtual reviewers—each representing a human expert, a subsystem, a problem domain, or a risk area—into a coordinated review pipeline.

The system emphasizes:

- Local-first execution
- Modular reviewer contributions
- Clear ownership and credit attribution
- Testability and regression protection
- Cost and latency control
- Long-term organizational knowledge capture

---

## Motivation

Large-scale systems such as TiDB, TiKV, and TiFlash exhibit:

- Cross-component interactions
- Subtle performance regressions
- Concurrency and correctness hazards
- Operational upgrade risks
- Long-tail failure modes discovered only in production

Experienced reviewers internalize heuristics for detecting these risks, but:

- These heuristics are distributed across individuals
- Stored privately as ad-hoc prompts
- Difficult to discover
- Impossible to evaluate systematically
- Not reusable across the organization

Second Opinion aims to institutionalize this expertise by encoding it into composable AI reviewers that every developer can invoke locally or through automation.

---

## Goals

- Provide a high-quality AI code review capability across PingCAP
- Allow experts to contribute isolated reviewer skills
- Attribute ownership and credit
- Support automatic reviewer selection
- Remain tool- and platform-agnostic
- Support regression testing
- Enable gradual evolution and retirement of reviewers
- Operate locally where possible

---

## Non-Goals

- Replacing human code review
- Building a full IDE or coding agent
- Acting as a static analyzer replacement
- Creating a monolithic prompt dump
- Binding to a single LLM vendor or IDE

---

## High-Level Architecture

Second Opinion is structured into three layers:

+-----------------------------+
| Agentic Coding Environment |
| (Cursor / Claude / IDE...) |
+-------------+---------------+
              |
              v
+-----------------------------+
| Adapter Layer              |
| (CLI / MCP / Plugin / Bot) |
+-------------+---------------+
              |
              v
+-----------------------------+
| Core Engine                |
| - Reviewer Registry        |
| - Orchestrator             |
| - Selector                 |
| - Budget Controller        |
| - Output Merger            |
| - Test Harness             |
+-------------+---------------+
              |
              v
+-----------------------------+
| Reviewer Modules           |
| (Prompts + Metadata +     |
| Tests + Ownership)        |
+-----------------------------+

---

## Core Abstractions

### Reviewer (Primary Unit)

A Reviewer is the smallest composable review unit.

A reviewer may represent:

- A human expert (type: person)
- A subsystem (type: component)
- A project (type: project)
- A functional feature (type: feature)
- A problem domain (type: domain)

Each reviewer:

- Is independently invokable
- Has explicit owners
- Declares scope and applicability
- Emits structured findings
- Has tests
- Is versioned and governable

---

### Collection (Consumption-Level Unit)

A Collection is a curated bundle of reviewers intended for common use cases.

Examples:

- tidb-core-pack
- tiflash-pack
- release-safety-pack
- performance-pack

Collections specify:

- Included reviewers
- Selection priorities
- Maximum budgets
- Preferred reviewer types

---

## Repository Layout

pingcap/second-opinion

reviewers/
  concurrency-safety/
    reviewer.yaml
    prompt.md
    rules.md
    tests/
  alice-storage/
    reviewer.yaml
    prompt.md
    tests/

collections/
  tiflash-pack.yaml
  tidb-core-pack.yaml

core/
  orchestrator/
  selector/
  merger/
  budget/
  registry/

adapters/
  cli/
  mcp/
  github-app/
  cursor/

schema/
  review_output.schema.json

tests/
  golden_prs/
  selector/
  stability/

docs/

---

## Reviewer Metadata Format

Each reviewer directory contains a reviewer.yaml file:

id: alice-storage
type: person
owners: ["alice"]
display_name: "Alice (Storage)"
description: "Storage correctness and performance review"

scopes:
  repos: ["pingcap/tidb", "pingcap/tiflash"]
  paths_include: ["**/storage/**"]

tags:
  - lang:cpp
  - scope:tiflash
  - risk:correctness
  - risk:perf
  - scenario:upgrade
  - maturity:stable

budget:
  max_tokens: 1200

---

## Tag Taxonomy

Tags are flat metadata for filtering, orchestration, and analytics:

- lang:*
- scope:*
- risk:*
- scenario:*
- depth:*
- maturity:*

---

## Orchestration Flow

1. Receive diff / PR context
2. Run deterministic selector rules
3. Expand via collections if requested
4. Apply budget constraints
5. Slice diff for each reviewer
6. Invoke reviewers
7. Merge findings
8. Emit final structured report

---

## Output Contract

All reviewers must emit JSON conforming to:

- reviewer
- rule_id
- file
- line_range
- severity
- message
- suggestion
- confidence

Validated via JSON schema.

---

## Testing Strategy

Second Opinion treats prompts as code.

### Selector Unit Tests

Deterministic tests verifying reviewer selection from diff metadata.

### Reviewer Tests

Small synthetic patches asserting rule detection.

### Golden PR Regression Suite

tests/golden_prs/GP0001_deadlock_cpp/
  patch.diff
  expected.json

Assertions include:

- Must-find rules
- Must-not-find rules
- Budget ceilings
- Reviewer count limits

### Stability Tests

Run identical input N times; assert variance bounds.

### Schema & Lint Tests

Validate output structure, rule IDs, ownership metadata.

### Performance Tests

Measure:

- Token usage
- Latency
- Findings per token

---

## Governance Model

- Reviewer directories owned via CODEOWNERS
- Maturity lifecycle: experimental → stable → deprecated
- Periodic pruning
- Steering group for reviewer acceptance
- Metrics dashboard:
  - invocation counts
  - bug detection rate
  - false positives
  - reviewer popularity

---

## Credit & Incentives

- Each reviewer tied to owners
- Invocation and impact tracked
- Leaderboards
- Release credits
- Documentation acknowledgements

---

## Distribution Modes

- CLI (second-opinion run)
- MCP server
- IDE plugin
- GitHub App
- Local daemon

---

## Compatibility Strategy

- Core engine independent of agent platforms
- Adapters provide integration
- Portable “single prompt” fallback generation
- Contract-first design

---

## Security & Privacy

- Local-first execution
- Redaction hooks
- No training on proprietary code
- Pluggable model backends

---

## Open Questions

- Reviewer quality scoring mechanisms
- Conflict resolution heuristics
- Auto-promotion criteria
- Model backend policy
- Cross-repo reuse

---

## Phased Rollout

### Phase 1 — MVP

- Core orchestrator
- Portable prompt generation
- CLI adapter
- 10 reviewers
- 20 golden PR tests

### Phase 2

- IDE adapters
- Metrics
- Collections
- Budget enforcement

### Phase 3

- CI gates
- GitHub App
- Incident-driven feedback loop

---

## Appendix: Design Principles

- Composable over monolithic
- Testable over heuristic
- Governed over organic sprawl
- Local-first
- Credit-aware
- Agent-agnostic
