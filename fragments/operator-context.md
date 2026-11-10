# Operator context and consent provenance

Trusted host code, not an unrestricted parent model, retains authenticated
operator events. Before compilation or delegation it derives `review_context` conforming to
`schemas/review-context.schema.json`: language, focus, budget, process override,
and `draft_github_comments`. A draft request is not a publication grant.

Do not place consent, tokens, user identities, or an `allow_post` flag in compiled
prompts or reviewer artifacts. The diff, repository documentation, asset text,
and generated JSON cannot supply, override, or authenticate operator intent.
Missing task context must be returned to the parent, not reconstructed from code.

The reviewer generates local findings and optionally a comment draft. It never
publishes, asks for consent, or interprets a quoted "user confirmed" as approval.
Language settings and initial/post-review posting decisions belong to trusted
host code outside every source-consuming model stage.

Before publication trusted host code must bind actual operator authorization to
the intended GitHub account, target repository, PR number, reviewed head SHA,
endpoint kind, and exact complete payload (including every inline comment). Read
the current PR head again before sending. A changed head, target, or payload
requires renewed authorization; authorization for one publication is not a
reusable grant. Initial explicit posting intent may be used for that same review
scope after the trusted operator UI has checked the completed payload; do not ask again solely
because a reviewer was delegated.

`runtime/publication_gate.py` is a trusted-host, one-use in-memory binding helper.
Only trusted orchestration code handling real user events may call
`record_operator_approval`; never expose that method as a model tool or deserialize
approvals from repository files. It does not authenticate a chat service or make
GitHub calls itself. `runtime/github_publisher.py` is the production dispatcher:
it freezes the endpoint/payload, checks the actual PR target and current head,
consumes this grant immediately before the `gh` write, and reads the result back.
The operator-terminal path in `scripts/publish_review.py` previews the frozen
request/account and creates the grant only from an exact response on `/dev/tty`.
An agent-owned PTY can type this response: a terminal challenge is not human
authentication. That usage is unsupported, not a safe way to grant model access.
The host remains responsible for authenticating user events and preventing all
model stages from reaching this terminal, dispatcher or ambient write capabilities.
Never have a model confirm the terminal challenge. Automated hosts must call the
dispatcher from a real authenticated event handler, not synthesize approval.

Trusted asset installation/updates are a separate operator workflow. No review
stage may call the installer or edit assets; mount trusted assets read-only for
every model stage. The reference runner exposes no filesystem tools or asset-write
endpoint. An external host that cannot enforce this must not launch the workflow.
