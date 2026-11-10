# Pinned production assets

Choose the trusted installation before loading any reviewed source. Run its
`scripts/asset_bundle.py --review-root /path/to/reviewed/tree` from trusted host
code, and provide the returned assets to the tool-free tagger/compiler/reviewer.
The root comes from the loader's own module location. There is no asset-root flag,
project-local lookup, CWD search or `taxonomy.md` discovery fallback. Missing assets,
symlinks, and an installation nested in (or enclosing) the target tree are refused.
`scripts/review_only.py` requires `--review-root` and compiles the actual review
criteria in trusted Python before provider I/O. It does not accept `--compiled`,
external compiled prompts, provenance assertions, or model-selected asset paths.
All production policies and experts are included in stable path order; the
operator chooses `pr-review` (default) or `review-branch` with `--process`.
Priority/exclusive/activation metadata cannot displace mandatory policies.
This conservative mode trades prompt size and relevance for a smaller trusted
boundary: it needs no model tagger/compiler at all. Language and focus limit the
assessment, not the mandatory side-effect restrictions.

The exact compiled criteria and SHA-256 of each consumed asset are written as
`second_opinion_meta.json` alongside findings. These are an audit record, not an
input or transferable authorization. Missing mandatory policies/workflows/output
contracts fail closed. Output directories inside the trusted install are refused.
The criteria are attached to the trusted instructions; diff and optional evidence
remain separate user data. No prompt text from the target can select policies.

Run the loader/runner from an operator-controlled installation, never a copy in
the branch being reviewed. Executing hostile Python cannot establish its own
trust. The host must keep that installation read-only to every model stage and
remove filesystem/network/mutation capabilities; an unrestricted external host
is not hardened merely by installing this skill. Fail closed if that separation
cannot be enforced. A target's project-local skill files remain review evidence.

Production exports omit experts/foo, processes/foo, policies/foo.yaml,
fragments/foo.md, examples and test fixtures. Sample source assets remain available
to contributors but do not enter the production bundle. Test fixtures can still be
exported only through the explicit test harness opt-in; the production bundle
never includes them, and production installation has no fixture-enabling CLI flag.

Installation refuses existing destinations, source symlinks and destinations
nested within the source. Keep the source checkout and install separate. Updates
are a separately authorized operator operation, not part of a model review.
Global Codex and Claude homes are conventional locations, not an automatic trust
decision: the trusted host pins the actual installation identity and path.

Legacy model tagger/compiler prompts remain contributor references for restricted
host integrations, not the supported reference CLI's execution path. Integrations
must use this deterministic compiler or independently enforce equivalent input
provenance; loading a bundle and then accepting an unrelated compiled prompt is
not a supported integration.

Invoke the loader and reviewer CLI with `python3 -I` and absolute trusted script
paths. Isolated Python ignores hostile CWD/PYTHONPATH/user-site imports; the CLI
refuses non-isolated direct execution. Imported APIs are for trusted host code.
