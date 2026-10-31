# `test_positional_import_nested_merges_in_place.py`

## Intent

Check one expected nested result for a positional import in the `nested` YAML
fixture.

## Setup and assertion

The test loads the `nested` profile from `tests/config` and asserts:

```python
config["etl"]["jobs"]["etl"]["jobs"]["foo"] == "bar"
```

This is evidence that the checked value appears at that path for the current
fixture.

## Limits

The test has one assertion. It does not check sibling preservation, import
trace contents, CLI output, or all positional import locations. It is a
targeted regression test, not a general guarantee of import behavior.

## Run

From `sprig-config-module/`:

```bash
poetry run pytest tests/test_positional_import_nested_merges_in_place.py
```
