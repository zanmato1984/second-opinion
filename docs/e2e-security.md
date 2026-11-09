# Safe E2E and review preparation defaults

Live model tests remain opt-in (`CODEX_E2E=1`). Set `CODEX_E2E_API_KEY` to a
dedicated, limited-budget test key. The harness no longer loads personal
`auth.json` or `config.toml`, nor uses ambient `OPENAI_API_KEY`. The old
`CODEX_E2E_AUTH_SOURCE` and `CODEX_E2E_CONFIG_SOURCE` overrides are not supported.

The harness uses a temporary HOME and CODEX_HOME, a fixed configuration,
workspace-write sandboxing, no sandbox network access, and a minimal child
environment. Model-generated shells do not inherit the API key. Sandbox
failures must fail the test; there is no unsandboxed fallback. The Codex
executable is resolved before replacing PATH with the operating system default.

This reduces exposure; a temporary HOME is not an OS security boundary, and the
CLI process still needs the dedicated API key to contact its model provider.
Run adversarial or external-repository E2E in a disposable, credential-minimal
OS environment. Do not treat this harness as isolation from all host-readable
files or as the production reviewer permission boundary.

Production test installations use an asset allowlist. Only the fixture test
explicitly installs `tests/fixtures` and the test-only skill into its temporary
skill home. Fixtures remain in source control for tests.

The branch preparation helper rejects plaintext HTTP/Git transports and requires
HTTPS github.com PR URLs. SSH review remotes remain supported. It creates a new
review branch/worktree, refuses existing paths or branches, and does not delete
or reset previous work. Base merging is now opt-in with `--merge-base`;
`--no-merge-base` is retained as an explicit spelling of the default. No remote
push or merge is performed.
