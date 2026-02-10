# re2 process workflow

- workflow_id: RE2-WORKFLOW-001
  name: Invariant-first adversarial deep review
  body: |
    This is the stronger, constraint-heavy variant of RE. It promotes invariants
    and critical assumptions to first-class review artifacts and introduces
    high-risk triggers plus an adversarial scenario matrix to catch hidden
    correctness bugs (mismatches, lost objects, duplicate naming, unstable
    ordering).

    Mandatory principles:
    - Coverage first: do not only read changed lines; trace potential impact to
      callers, config, data, security, performance, compatibility, observability,
      and operations.
    - Evidence first: every conclusion needs evidence (code location, call chain,
      tests, runtime output, or spec/document basis).
    - Invariants and assumptions first: list required invariants and key
      assumptions, each with a verification or falsification path. Prioritize
      order, pairing, naming, and ID fragility.
    - Assumptions must be verifiable: output must include an Assumption Ledger.
      Each assumption must be checked by reading code and cite evidence (file +
      symbol/position). If no code evidence was read, it cannot be Confirmed and
      cannot support High-confidence conclusions.
    - Every change must prove necessity: for each diff hunk, write purpose,
      mechanism, and a falsifiable counterfactual. If you cannot produce a
      falsifiable counterfactual, treat the change as deletable and record it as
      an issue (Severity: Low, Confidence: High).
    - Side effects must have a single owner: log/cleanup/retry/metrics/state
      changes must have a clear owner (usually boundary/sink). If the outer layer
      must perform the same effect under the same guard, the inner layer must not
      duplicate it unless it adds missing information or changes semantics
      (leak prevention, idempotency, or missing dimensions).
    - No "maybe": Medium/Low confidence requires a second check. Blocker/High
      severity requires second confirmation with complementary evidence.
    - Complex control flow is high risk: any new or expanded error-handling,
      cleanup, or retry complexity must be treated as high risk. Enter the
      adversarial scenario matrix and include at least one High-severity warning
      unless code evidence proves the complexity is minimal and necessary. If it
      is not minimal, propose a simplification and verification path.
    - Make doubts explicit: any plausible but unconfirmed risk must be listed in
      Findings (low severity, low confidence) with the shortest verification.
    - Fix the class: when a PR fixes or optimizes a pattern, scan similar usages
      and sibling paths. If not fixed, provide evidence and the shortest
      verification path.

    Workflow (execute in order):
    0) High-risk trigger patterns (if any hit, upgrade verification):
       - Sorting or reorder (sort/slices.Sort*, reorder by ID/name, map order)
       - ID rewrite or reuse (in-place mutation, overwrite old IDs, reuse temps)
       - Rename/swap/move (rename, swap positions, migrate/merge objects)
       - Parallel slice index alignment (for i := range A { use B[i] }) when A/B
         can be reordered or from different sources
       - Temp object overwrite (temp/hidden/tombstone replaced by later steps)
       - Complex cleanup/retry control flow (defer + explicit cleanup + internal
         retry; implicit idempotency assumptions)
       - Side-effect duplication or ownership overlap across error paths

    1) Scope:
       - Confirm review inputs: diff/commit/PR/patch/file list.
       - List change surface: add/delete/refactor/behavior/default/dep/config
         changes.
       - Scale model anchor (worst case unless proven otherwise):
         N_tidb >= 100, Data >= TB, N_obj >= 1e6, concurrency per node dozens to
         hundreds of goroutines. If not applicable, justify with code evidence.
       - Write invariants list (>= 5): conditions that must always hold.
       - Write key assumptions (>= 5) with shortest falsification path (code
         point/search/assertion/UT/min SQL). Include frequency, full-scan,
         allocation/lock contention, fanout, cache size ceilings when relevant.
       - Mark high-risk areas: concurrency, persistence/migration, state machines,
         compatibility, public interfaces/user-visible output.

    1.5) Assumption verification pass (required):
       - Use rg/call chains to locate the code point that carries each
         assumption.
       - Read the code and mark each assumption as:
         Confirmed (explicit guarantee or test), Contradicted, or Unknown.
       - Unknown must include the shortest next step (one command or next file).

    1.6) Necessity proof pass (required):
       - For each diff hunk, write 3-5 lines with:
         Purpose, Mechanism, Counterfactual (falsifiable; anchored to code or
         tests).
       - If no falsifiable counterfactual exists, mark as candidate deletion and
         record in Findings.

    1.7) Effect ownership / dominance pass (required):
       - Treat log/cleanup/free/retry/backoff/metrics/state-mutate/default or
         config change/user-visible output as effects.
       - For each new or modified effect:
         1) mark owner layer (helper/leaf vs boundary/sink)
         2) check dominance: does outer layer inevitably perform the same effect
            under the same guard?
         3) if yes and no extra info/semantics, treat as redundant and remove or
            move to owner.
       - Adversarial scenario matrix should include: high-frequency failure
         (avoid log spam and cleanup thrash), cancellation/timeout cleanup, and
         partial progress + retry (idempotency/resource existence).

    2) Blast radius mapping:
       - Entry/interface: public API, config/schema/storage format, error text,
         user-visible output.
       - Callers/dependencies: confirm caller semantics still hold.
       - Runtime behavior: defaults, feature flags, rollback/restore, old data or
         old client compatibility.

    2.5) Similar usage scan (required for fixes/optimizations):
       - Define the problem pattern and trigger conditions, plus the fix
         strategy.
       - Use rg/call chains to find similar usages or sibling paths.
       - For each hit: needs fix / does not need fix (reason + evidence) / unknown
         (shortest verification step). No "maybe".

    3) Deep verification by category (each must be Confirmed or N/A):
       - Correctness: edges, error branches, resource release, idempotency,
         state convergence.
       - Invariant review: map each invariant to evidence; watch ordering/ID
         rewrite/index alignment/object overwrite mismatches.
       - Security: validation, injection, authn/authz, sensitive leaks.
       - Data/consistency: transactions, concurrency, migration/backfill,
         retry semantics, old data compatibility.
       - Performance: cost model = frequency x per-call cost x scale model;
         confirm frequency or label Unknown with shortest verification.
       - Observability: logs/metrics/traces and diagnostic signal.
       - User-visible contract: SHOW/information_schema/errors/output stability.
       - Tests/docs: missing tests, doc updates for behavior changes.

    4) Second confirmation (required):
       - Trigger if Confidence is Medium/Low or Severity is Blocker/High.
       - Perform a different verification method and repeat the reasoning:
         broader read, minimal test, or history (git blame/commit).
       - Blocker/High requires at least two complementary evidence types.
       - Adversarial scenario matrix (>= 3) must be included.
       - If still unknown, state missing info and shortest next step.

    Output format (mandatory):
    - Write the structured sections below to review.md.
    - review.json must follow the repository schema: each finding includes file,
      lines, source, tags, severity, and message. Encode
      Confidence, What, Assumptions, Evidence, Impact, Fix, and Verify inside
      the message field when needed.

    review.md sections:

    Conclusion:
    - 1 to 3 bullets summarizing overall risk and merge recommendation.

    Assumption Ledger (required):
    - At least 5 assumptions. Each includes:
      A#: Assumption
      Status: Confirmed | Contradicted | Unknown
      Evidence: file + symbol/position
      Next: shortest verification step if Unknown

    Checklist:
    - Correctness / Invariants / Security / Data / Performance / Compatibility /
      Observability / User-visible contract / Tests / Docs, each with evidence or
      N/A.

    Findings (sorted by severity then confidence):
    - Severity: Blocker | High | Medium | Low
    - Confidence: High | Medium | Low
      - Medium/Low must state second-check action.
      - Blocker/High must include second confirmation with complementary
        evidence.
    - What: localized, reproducible issue description
    - Assumptions: list A# and status; if any Unknown, do not claim High
      confidence.
    - Evidence: code/command/output/spec
    - Impact: blast radius and worst-case outcome
    - Fix: minimal change preferred
    - Verify: how to validate (test/command/scenario)

    Regression test threshold (strong requirement):
    - If the change affects metadata, state machines, compatibility, or
      user-visible contracts, state whether to add at least one minimal
      regression test and justify the choice.

    Optional appendix: domain invariant library
    - Metadata: name uniqueness (case-insensitive), ID<->object bijection,
      pairing not dependent on slice order, deletes leave no residue.
    - State machines: convergence, recoverability, no illegal intermediate
      states visible.
    - User-visible: SHOW/information_schema outputs stable and no internal
      prefixes leak.
