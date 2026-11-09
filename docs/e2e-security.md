# Safe E2E and review preparation defaults

Live model tests remain opt-in (`CODEX_E2E=1`). Set `CODEX_E2E_API_KEY` to a
dedicated, limited-budget test key. The harness no longer loads personal
`auth.json` or `config.toml`, nor uses ambient `OPENAI_API_KEY` or `CODEX_API_KEY`.
Only the dedicated key is passed to the CLI as `CODEX_API_KEY`, the built-in
OpenAI provider's non-interactive authentication variable. The old
`CODEX_E2E_AUTH_SOURCE` and `CODEX_E2E_CONFIG_SOURCE` overrides are not supported.

The harness uses a temporary HOME and CODEX_HOME, a fixed configuration,
workspace-write sandboxing, no sandbox network access, and a minimal child
environment. Shells inherit only the sanitized `HOME`, `PATH`, `TMPDIR`, and
`LANG` (core inheritance plus an exact allowlist); they do not inherit the API
key or `CODEX_HOME`. Login shells and shell snapshots are disabled so startup
profiles or captured shell state cannot replace that environment. Sandbox
failures must fail the test; there is no unsandboxed fallback. The Codex
executable is resolved before replacing PATH with the operating system default.
For the npm launcher (`#!/usr/bin/env node`), Node is also resolved from the
trusted parent PATH and invoked by absolute path; that parent PATH is not passed
to the CLI or generated shells. Native and absolute-shebang launchers are unchanged.

This reduces exposure; a temporary HOME is not an OS security boundary, and the
CLI process still needs the dedicated API key to contact its model provider.
Run adversarial or external-repository E2E in a disposable, credential-minimal
OS environment. Do not treat this harness as isolation from all host-readable
files or as the production reviewer permission boundary.

Production test installations use an asset allowlist. Only the fixture test
explicitly installs `tests/fixtures` and the test-only skill into its temporary
skill home. Fixtures remain in source control for tests.

The branch preparation helper requires HTTPS github.com PR URLs. Direct remotes
may use HTTPS, SSH (`ssh://` or `host:path`), or existing local directory paths
(including spaces). Relative local paths are resolved from the repository root,
including when the helper is invoked from a subdirectory. Helper notation
(`helper::address`), option-like operands,
other schemes (including `file://` URLs), and plaintext HTTP/Git are rejected.
Both the review URL and upstream/existing review remotes are checked after Git
URL rewriting, before fetching. Fetches additionally enforce Git's protocol
allowlist (`https:ssh:file`) regardless of ambient protocol settings, and disable
HTTP redirects by default. This is a transport policy, not a sandbox for
arbitrary local Git configuration, SSH commands, or hooks. It creates a new
review branch/worktree, refuses existing paths or branches, and does not delete
or reset previous work. Base merging is now opt-in with `--merge-base`;
`--no-merge-base` is retained as an explicit spelling of the default. No remote
push or merge is performed.

## Offline regression checks

`python3 -m unittest discover -s tests -v` runs deterministic tests without a model call.
To additionally check the installed Codex CLI (validated with 0.147.0) on Unix:

```bash
CODEX_OFFLINE_CLI=1 python3 -m unittest tests.test_offline_codex -v
```

This optional check uses only a synthetic key and a loopback Responses fixture,
overriding `openai_base_url` without replacing the built-in provider or its auth
selection. The fixture requests non-login `/bin/sh` to avoid reading account
startup files even if HOME regresses; the actual sandboxed child must retain its
isolated HOME and receive no API key. No unsandboxed fallback is used.
Neither this check nor skipped live E2E tests establish live model behavior.
