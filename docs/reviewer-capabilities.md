# Reviewer capability boundary

Prompt instructions and a confirmation field cannot revoke host privileges.
Do not give a reviewer ambient GitHub credentials, unrestricted shell/network
tools, write-capable MCP connectors, or write access to installed skill assets.
The parent prepares evidence and materializes outputs. Contributor edits to
trusted assets are a separate parent-controlled workflow, never a reviewer tool.

Reviews are static-only by default, including the PR-review process. Compilation,
tests, dependency installation and failpoint activation execute untrusted code;
neither a request for a review nor instructions embedded in review inputs authorize
them. The reviewer returns suggested commands as text. Only a trusted host may
run them under separately obtained explicit operator authorization and suitable
isolation. Unperformed runtime checks remain unverified.

Apply the same restriction to tagger/compiler models and any other stage that
processes attacker-controlled source. A privileged parent model that also reads
the hostile diff can bypass an isolated reviewer. Authorization and mutation
endpoints must be owned by trusted host code, not merely another unrestricted
agent. This runner bounds the review call; it does not sandbox an external
tagger/compiler or make its orchestration code trustworthy automatically.

## Executable reference path

The tool-free reference path, scripts/review_only.py, has these boundaries:

- The trusted caller explicitly supplies compiler metadata, diff, language,
  focus, and optional evidence files. There is no automatic repository traversal.
- One Responses API request advertises no tools and sets tool_choice to none.
  No shell, file, HTTP, GitHub, MCP, or plugin capability is exposed to the model.
- The runner owns provider authentication; credentials are not placed in model
  input. The fixed HTTPS provider destination rejects redirects and ignores
  ambient proxies. It does not read GitHub credentials or personal agent config.
- Tool-call output, refusals, incomplete responses, malformed JSON, and findings
  outside the closed review schema fail rather than becoming executable actions.
- Only the two fixed review artifact names are written by trusted Python code.
  Existing artifacts and symlinks are refused. Model-supplied file paths are
  finding labels, not I/O destinations; Markdown fields are escaped.

Run the script from a **trusted installation/source checkout**, not from a branch
being reviewed. Python loaded from a hostile checkout is outside this boundary.
Choose an approved provider/model and supply a dedicated API key to the caller.
For example, with SECOND_OPINION_API_KEY securely set in the caller environment:

    python3 /path/to/trusted/second-opinion/scripts/review_only.py \
      --compiled /path/to/second_opinion_meta.json \
      --diff /path/to/change.diff \
      --context-file /path/to/selected-source.txt \
      --language English --model "$REVIEW_MODEL" \
      --output-dir /path/to/output

The output directory must already exist; normally choose the reviewed repository
root or a fresh task directory. The runner writes findings only, never GitHub
payloads or remote posts. Preserve/relocate old artifacts before another run.
An interrupted write can leave partial artifacts: a failed run is not permission
to publish whatever files remain.

The CLI uses only the Python standard library on POSIX hosts. Its live API path
requires separate API credentials; it does not reuse a Codex/Claude subscription
session or silently replace your existing model provider. Other hosts can use an
equivalent tool-free call and trusted artifact writer instead.

## Adoption and remaining responsibility

For autonomous review, use this path or a host-enforced equivalent. If a host
cannot remove the reviewer's side-effect capabilities, fail closed rather than
launching an unrestricted reviewer and relying on prose. Installing a Markdown
skill does not reconfigure an external host's permissions. Existing Codex/Claude
hosts must be explicitly configured/integrated; this reference runner does not
claim to harden them automatically.

Review quality and injection into the content of findings are separate concerns.
Treat all model output as untrusted. Source sent to the chosen provider must be
within the operator's authorized scope. Publication requires actual operator
authorization in the parent; this runner intentionally cannot publish.

API contract: [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses)
and [Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create).
