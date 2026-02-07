# Second Opinion – User Journey

This is a realistic, end-to-end walkthrough of how a developer uses Second Opinion locally.

## 1) Get the code

```
git clone https://github.com/zanmato1984/second-opinion.git
cd second-opinion
```

## 2) Set up Python (conda base)

```
conda run -n base python -m pip install pytest jsonschema PyYAML
```

## 3) Run the review pipeline

Use the built-in golden diff to see the system end-to-end:

### 3a) Select reviewers

```
conda run -n base python -m adapters.cli select \
  --repo pingcap/tidb \
  --diff tests/golden_prs/GP0001_deadlock_cpp/patch.diff
```

### 3b) Assemble prompts

```
conda run -n base python -m adapters.cli assemble \
  --repo pingcap/tidb \
  --diff tests/golden_prs/GP0001_deadlock_cpp/patch.diff
```

The output includes a `final_prompt` field that is the exact prompt to send to the final review model.

### 3c) Run the final review

```
conda run -n base python -m adapters.cli review \
  --repo pingcap/tidb \
  --diff tests/golden_prs/GP0001_deadlock_cpp/patch.diff
```

Expected behavior:
- The selector picks `concurrency-safety` based on scope/path filters.
- The prompt assembler includes reviewer prompt + diff slice deterministically.
- The reviewer rule matches back-to-back `lock()` calls.
- A JSON report is printed that conforms to `schema/review_output.schema.json`.

## 4) Run the full test suite

```
conda run -n base python -m pytest -q
```

Expected behavior:
- Selector tests pass
- Golden PR regression passes
- Stability test passes (ignores timestamps)
- Registry validation passes

## 5) Add a new reviewer (example workflow)

1. Create a new folder:

```
mkdir -p reviewers/io-safety
```

2. Add `reviewer.yaml` with scopes, tags, and rules.
3. Add `prompt.md` and `rules.md`.
4. Add a new golden PR diff under `tests/golden_prs/`.
5. Update or create tests to lock in detection.

Run tests again to validate the new reviewer.

## 6) Add a collection

Edit or add `collections/<collection-id>.yaml` with reviewer IDs:

```
id: release-safety-pack
reviewers:
  - concurrency-safety
  - io-safety
preferred_types:
  - domain
```

Then run:

```
conda run -n base python -m adapters.cli \
  --repo pingcap/tidb \
  --diff path/to/patch.diff \
  --collections release-safety-pack
```

## 7) Share results

- Save JSON output to a file with `--output out.json`.
- Attach results to a PR or share in CI logs.

---

This journey mirrors typical daily usage: diff → select → assemble → review → tests.
