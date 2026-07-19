# Exceptions

## `ConfigLoadError`

`ConfigLoadError` is the common public error for loading, parsing, imports,
secret handling, configuration injection, and dynamic instantiation.

```python
from sprigconfig import ConfigLoadError, load_config

try:
    cfg = load_config(profile="prod", config_dir="config")
except ConfigLoadError as error:
    raise SystemExit(f"Configuration failed: {error}") from error
```

Typical causes include:

- unsupported configuration formats;
- missing `APP_CONFIG_DIR` when no directory is supplied;
- invalid YAML, JSON, or TOML;
- missing, invalid, escaping, or circular imports;
- invalid or unavailable Fernet keys when a secret is decrypted;
- invalid injection or `_target_` configuration.

Missing root and profile files currently produce empty layers rather than an
exception. Check required files in application startup when your deployment
policy demands them.

## `ConfigValidationError`

`ConfigValidationError` extends `ConfigLoadError`, so existing broad error
handlers continue to work:

```python
from sprigconfig import ConfigLoadError, ConfigValidationError

assert issubclass(ConfigValidationError, ConfigLoadError)
```

It is raised only when `schema=` is supplied and the merged configuration does
not match the dataclass schema. See [Schema Validation](../schema-validation.md).

## Handling errors

Catch the narrow exception when validation needs different reporting:

```python
try:
    cfg = load_config(profile="prod", config_dir="config", schema=AppSchema)
except ConfigValidationError as error:
    print(f"Invalid configuration shape: {error}")
except ConfigLoadError as error:
    print(f"Could not load configuration: {error}")
```

Do not log decrypted secret values or dump configuration with `safe=False` in
an exception handler.
