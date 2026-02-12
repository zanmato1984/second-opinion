# TiDB Vectorized Testing

- Prefer existing vectorized test frameworks in `pkg/expression/`:
  - `testVectorizedBuiltinFunc` / `testVectorizedEvalOneVec` in `pkg/expression/bench_test.go`
  - `TestVectorizedBuiltin*` in `*_vec_test.go` and `*_vec_generated_test.go`
- Add cases to existing vectorized tables instead of introducing new files where possible.
- Ensure tests compare `vecEval*` vs row-based `eval*` per-row, including null bitmap and warning count checks.
- Use chunks with size > 1 and include nulls; for non-deterministic functions, assert invariants rather than strict equality.
- If vectorized execution is intentionally unsupported, call it out explicitly and ensure tests reflect that.
