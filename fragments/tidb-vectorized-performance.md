# TiDB Vectorized Performance

- Batch-first evaluation: avoid per-row `eval*` in `vecEval*` loops; operate on column slices.
- Minimize allocations: call `result.ResizeXXX`/`ReserveXXX` once and reuse buffers; avoid per-row `Append*`.
- Avoid Datum conversions: prefer typed accessors (for example `Int64s()`, `Float64s()`, `Decimals()`) over `GetDatum`.
- Null handling cost: short-circuit for all-null inputs and set nulls only when needed.
- Selection vector aware: when `sel` is present, iterate `sel` and skip filtered-out rows.
- Type-specific fast paths: keep hot paths on common types and sizes; avoid reflective or interface-heavy calls in loops.
- Warnings/errors: preserve warning behavior without per-row overhead where possible; aggregate when safe.
