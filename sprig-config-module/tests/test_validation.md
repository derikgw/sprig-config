## Purpose

Validates opt-in schema validation behavior for `ConfigLoader` using typed dataclass schemas.

## Coverage

- Successful validation against a matching schema.
- Missing required key detection.
- Type mismatch detection with dotted-path diagnostics.
- Unknown key rejection.
- Nested path error reporting.
- Backward-compatible loading when no schema is supplied.
- Proof that the validator is never invoked on the legacy no-schema path.
- A config value that conflicts with a code-side schema type still loads when
  `schema=` is omitted.
- Validation through both `ConfigLoader` and `load_config`.
- Optional/defaulted fields and typed list/dict values.
- Validation after imports and profile overlays are merged.
- Runtime-generated metadata outside the user schema.
- Format parity across YAML, JSON, and TOML.
- Clear rejection of non-dataclass types and dataclass instances.

## Why this matters

Schema validation should fail fast with precise diagnostics while remaining fully opt-in and backward-compatible for existing users who do not provide a schema.
