# TiDB Vectorized Parity

Use this when changes touch scalar builtin functions (for example under `pkg/expression/`).

- Identify scalar builtin changes (new/modified `builtin_*.go`, signatures, or behavior changes).
- Locate vectorized counterparts (`*_vec.go`, `*_vec_generated.go`) and apply the same semantic updates.
- Verify `vectorized()` returns true when the function supports vectorized execution and uses the updated path.
- Same bug, same fix: if scalar evaluation is fixed, check whether vectorized evaluation needs the same fix.
- Cover all variants/signatures so no vectorized path is left behind.
- Ensure row-based `eval*` and `vecEval*` match for nulls, warnings, overflow/truncation, collation/timezone, and error types.
