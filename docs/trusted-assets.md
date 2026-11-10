# Pinned production assets

Choose the trusted installation before loading any reviewed source. Run its
`scripts/asset_bundle.py --review-root /path/to/reviewed/tree` from trusted host
code, and provide the returned assets to the tool-free tagger/compiler/reviewer.
The root comes from the loader's own module location. There is no asset-root flag,
project-local lookup, CWD search or `taxonomy.md` discovery fallback. Missing assets,
symlinks, and an installation nested in (or enclosing) the target tree are refused.
`scripts/review_only.py` requires `--review-root` and repeats this preflight before
provider I/O. A file claiming it was compiled from trusted assets is not proof of
provenance; the host must prepare inputs from this bundle, not hostile repository
files. The asset loader does not authenticate or sandbox a model-based compiler.

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
