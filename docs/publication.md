# Trusted publication boundary

`runtime/github_publisher.py` is an executable GitHub dispatch boundary, not a
model tool. It consumes a one-use `PublicationGate` immediately before the real
`gh api` POST. Repository, PR, current head, endpoint kind and the complete request
are bound. The dispatcher freezes input before any network I/O, refuses a
renamed/different PR target, and never retries or changes payload modes.
The request pins `commit_id`; the head recheck is not a server-side atomic
compare-and-swap against later GitHub updates.

Automated hosts must authenticate the real operator event outside model context,
show/check the exact completed request, create the gate there, and call
`GitHubPublisher.publish`. Do not accept approvals from files, model output or
review-context booleans. Keep all tagger/compiler/reviewer stages tool-free and
unable to invoke the publisher, its terminal or asset installers. This does not
reconfigure an existing unrestricted Codex/Claude host automatically. If the host
cannot enforce these capabilities, publication and autonomous review are disabled.

## Operator-terminal path

An operator can run the trusted installed entry point outside the reviewed tree:

```sh
python3 /path/to/trusted/second-opinion/scripts/publish_review.py \
  --repository owner/repository --pull-number 123 \
  --reviewed-sha "$REVIEWED_SHA" --request /path/to/request.json
```

There is no approval CLI flag or grant-file format. The entry point previews the
frozen JSON and requires the operator to type the target, full SHA and digest on
an operator-controlled `/dev/tty`. Never launch it from an agent's shell/PTY;
terminal possession is the host's responsibility, not proof of a human by itself.
The actual write still goes through the dispatcher and the same one-use gate.

The request has exactly `kind` and `payload`. For a submitted PR review use:

```json
{"kind":"review","payload":{"commit_id":"<full reviewed SHA>","event":"COMMENT","body":"Review feedback"}}
```

Events are COMMENT, APPROVE or REQUEST_CHANGES; pending reviews and ordinary issue
comments are unsupported. Inline review comments may be included in `comments`
with body, repository-relative path, positive line and side RIGHT. A single file
comment uses kind `comment` and payload fields commit_id, body, path and
subject_type `file` (no line or side). A single inline comment instead supplies
line and side RIGHT. Draft artifacts must be converted to these exact wire
requests before approval. Each request needs its own approval; a failed inline
anchor cannot authorize a file/general fallback.

The dispatcher reads the individual posted object back and checks commit, URL,
body and submitted review state (or comment anchor). A network/verification
failure after a POST is ambiguous: inspect GitHub before any new authorization
or retry. It does not automatically delete or duplicate a possibly posted object.

API shapes: [PR reviews](https://docs.github.com/en/rest/pulls/reviews#create-a-review-for-a-pull-request)
and [review comments](https://docs.github.com/en/rest/pulls/comments#create-a-review-comment-for-a-pull-request).

## Trusted asset writes

Review models have no trusted-asset write endpoint. In the reference path only
trusted Python writes fixed review artifacts; assets stay read-only. Installation
is a separately authorized operator operation, never part of reviewing a diff.
External hosts must enforce the same filesystem separation; documentation or a
PublicationGate alone cannot revoke a shell's write capability.
