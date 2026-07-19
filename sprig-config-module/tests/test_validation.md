## Purpose

Validates opt-in schema validation behavior for `ConfigLoader` using typed dataclass schemas.

## Coverage

- Successful validation against a matching schema.
- Missing required key detection.
- Type mismatch detection with dotted-path diagnostics.
- Unknown key rejection.
- Nested path error reporting.

## Why this matters

Schema validation should fail fast with precise diagnostics while remaining fully opt-in and backward-compatible for existing users who do not provide a schema.
