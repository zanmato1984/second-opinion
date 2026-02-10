---
name: my-second-opinion
description: "Contributor workflow for integrating individual review skills into the Second Opinion repo."
---

# My Second Opinion (Contributor Skill)

## Purpose

Guide contributors who provide an individual SKILL.md. Extract their process,
policy, fragment, and expert content, integrate shared parts into the repo, and
preserve attribution for the contributor's unique expertise.

## Scope & Trigger

Use when a contributor wants to add or integrate their review skill into this
repository. The contributor typically provides a SKILL.md or equivalent text.

## Safety & Preflight

- Operate on the current working directory as the target repo.
- Confirm these paths exist before edits: rfc.md, taxonomy.md, experts/, processes/, policies/, fragments/.
- Do not modify the main SKILL.md unless explicitly requested.
- If the repo structure is missing, stop and ask for confirmation or a new path.

## Workflow (Required)

1) Intake
- Ask for contributor handle/name and the SKILL.md text or path.
- Ask for any preferred attribution or naming constraints.

2) Parse and Classify
Split the provided content into these buckets:
- Process: multi-step workflow(s) with ordered steps and output contract.
- Policy: always-on guardrails or organization-wide constraints.
- Fragment: reusable formatting, checklists, output templates, evidence rules.
- Expert: atomic rules or heuristics with tags or scope.
- Unknown: unclear content (ask for clarification).

3) Process Admission Gate (Strict)
Because processes are scarce, compare the submitted process to existing ones:
- Goal overlap
- Workflow structure
- Activation/trigger conditions
- Cost/priority profile

If overlap is high, recommend merging or extending an existing process.
Only create a new process if it is materially distinct (new risk class,
workflow structure, or activation trigger).

4) Integration Proposal (Mandatory)
Propose:
- Which parts go to shared directories (fragments/, policies/, processes/)
- Which parts remain attributed under experts/<contributor>/ or processes/<id>/
- Any deduplication or refinement steps
- Naming choices for ids and files

5) Rationale Output (Mandatory)
Explain the reasoning for each integration choice. Example:
- "Moved checklist to fragments because it is reusable and non-attributed."
- "Kept concurrency heuristics under experts/<name> because it is personal."
- "Merged policy with existing security policy due to identical constraints."

6) Confirmation Gate (Mandatory)
Ask the contributor to confirm or revise the plan before applying changes.

7) Apply Changes
After confirmation:
- Create/update files in experts/, processes/, policies/, fragments/.
- Update tests if new assets are added (tests/test_reviewers.py or tests/test_assets.py).
- Keep changes minimal and focused on the approved plan.

8) Follow-up Loop
Stay available for further questions or adjustments until the contributor is
satisfied.

## Integration Rules

- Fragments: reusable guidance or formatting with no personal attribution.
- Policies: always-on constraints; name by domain (security, compat, etc.).
- Processes: curated workflows; require explicit justification.
- Experts: contributor-specific rules and heuristics.
- Deduplicate when overlap is high; preserve attribution notes in provenance or
  meta.yaml when merging.

## Output Style

- Provide a short plan summary, then the rationale, then ask for confirmation.
- Use concise, actionable wording.
