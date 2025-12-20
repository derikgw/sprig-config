# test_toml_support.py — TOML Format Support Tests

## Purpose

This test module verifies that `ConfigLoader` correctly supports TOML (`.toml`) configuration files alongside YAML and JSON formats.

TOML support enables users to write configurations using TOML syntax, which is particularly popular in the Python ecosystem (e.g., `pyproject.toml`).

---

## What This Tests

### 1. **Basic TOML Loading** (`test_toml_basic_loading`)

Verifies that:
- TOML files can be parsed correctly
- Nested TOML tables (e.g., `[app]`, `[server]`) are converted to Python dictionaries
- Values are accessible via dotted-key notation

### 2. **TOML with Imports** (`test_toml_with_imports`)

Tests the positional import feature with TOML files:
- Extension-less imports work (`imports = ["imports/database"]` resolves to `.toml`)
- Imported TOML content merges at the root level
- Proper structure: `imports` must be at root level in TOML (before any table headers)

**Important TOML Constraint**: Due to TOML syntax, the `imports` array must be declared at the root level before any table headers like `[app]`. This is a TOML language requirement, not a SprigConfig limitation.

### 3. **TOML Profile Overlays** (`test_toml_profile_overlay`)

Validates profile-based overrides using TOML:
- Base TOML config (`application.toml`)
- Profile overlay TOML (`application-dev.toml`)
- Deep merge semantics work correctly with TOML structures
- Profile values properly override base values

### 4. **Environment Variable Expansion** (`test_toml_env_var_expansion`)

Ensures environment variable substitution works in TOML files:
- `"${VAR}"` syntax expands to environment variable values
- `"${VAR:default}"` syntax provides fallback values
- Expansion happens before TOML parsing

---

## Why TOML Support Matters

TOML has become a standard configuration format in the Python ecosystem:
- `pyproject.toml` is the standard for Python project metadata
- TOML syntax is clean, readable, and strongly typed
- Many Python tools prefer TOML over YAML or JSON

By supporting TOML, SprigConfig allows teams to use a single configuration format across their entire Python project, from build configuration to runtime settings.

---

## Design Notes

### TOML Parsing

- Uses Python's built-in `tomllib` module (Python 3.11+)
- TOML files are read as text, environment variables are expanded, then parsed
- Parsing errors raise `ConfigLoadError` with clear messages

### Format Portability

The same import structure works across YAML, JSON, and TOML:

```toml
# application.toml
imports = ["imports/database", "imports/cache"]

[app]
name = "MyApp"
```

```yaml
# application.yml
imports:
  - imports/database
  - imports/cache

app:
  name: MyApp
```

The loader automatically resolves imports to the correct format based on the active `ext` setting.

---

## Related Tests

- `test_import_trace.py` - Verifies import tracking works across all formats
- `test_deep_merge.py` - Tests merge semantics that apply to all formats
- `test_profiles.py` - Profile overlay behavior is format-agnostic
