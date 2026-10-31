## Purpose

Validates opt-in schema validation behavior for `ConfigLoader` using typed dataclass schemas.

## Coverage

- Successful validation against a matching schema.
- Missing required key detection.
- Type mismatch detection with dotted-path diagnostics.
- Unknown key rejection.
- Nested path error reporting.
- Backward-compatible loading when no schema is supplied.
- A monkeypatched validator that raises if called, verifying it is not invoked
  for the tested legacy no-schema load.
- A config value that conflicts with a code-side schema type still loads when
  `schema=` is omitted.
- Validation through both `ConfigLoader` and `load_config`.
- Optional/defaulted fields and typed list/dict values.
- Validation after imports and profile overlays are merged.
- Runtime-generated metadata outside the user schema.
- Format parity across YAML, JSON, and TOML.
- Clear rejection of non-dataclass types and dataclass instances.

## Why this matters

These tests support opt-in schema validation for the listed dataclass schemas,
values, and formats. They do not cover every typing feature or every possible
schema error.

## Run

From `sprig-config-module/`:

```bash
poetry run pytest tests/test_validation.py
```
