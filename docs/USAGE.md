# Second Opinion Usage

## CLI

Run a review against a unified diff (default `review` command):

```
python3 -m adapters.cli --repo pingcap/tidb --diff path/to/patch.diff
```

Explicit `review` command:

```
python3 -m adapters.cli review --repo pingcap/tidb --diff path/to/patch.diff
```

Run with a collection (bundled reviewers):

```
python3 -m adapters.cli --repo pingcap/tidb --diff path/to/patch.diff --collections tidb-core-pack
```

Select reviewers only:

```
python3 -m adapters.cli select --repo pingcap/tidb --diff path/to/patch.diff
```

Assemble reviewer prompts deterministically (outputs a `final_prompt` for the final review step):

```
python3 -m adapters.cli assemble --repo pingcap/tidb --diff path/to/patch.diff
```

Output to a file:

```
python3 -m adapters.cli --repo pingcap/tidb --diff path/to/patch.diff --output out.json
```

Specify LLM backends (defaults to `mock` for local testing):

```
python3 -m adapters.cli review \
  --repo pingcap/tidb \
  --diff path/to/patch.diff \
  --selector-backend mock \
  --final-backend mock
```
