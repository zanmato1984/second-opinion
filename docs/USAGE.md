# Second Opinion Usage

## CLI

Run a review against a unified diff:

```
python3 -m adapters.cli --repo pingcap/tidb --diff path/to/patch.diff
```

Run with a collection (bundled reviewers):

```
python3 -m adapters.cli --repo pingcap/tidb --diff path/to/patch.diff --collections tidb-core-pack
```

Limit prompt budget:

```
python3 -m adapters.cli --repo pingcap/tidb --diff path/to/patch.diff --max-tokens 2000
```

Output to a file:

```
python3 -m adapters.cli --repo pingcap/tidb --diff path/to/patch.diff --output out.json
```
