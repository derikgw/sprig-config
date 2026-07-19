---
title: Schema Validation
---

# Schema Validation

Schema validation is optional. Existing applications that omit `schema=` use
the same loading behavior as before, even when configuration values do not
match annotations elsewhere in application code.

## Define a schema

Use standard dataclasses for nested configuration sections:

```python
from dataclasses import dataclass, field


@dataclass
class DatabaseSchema:
    host: str
    port: int


@dataclass
class AppSchema:
    database: DatabaseSchema
    features: list[str] = field(default_factory=list)
```

## Enable validation

Pass the dataclass type—not an instance—to either public loading API:

```python
from pathlib import Path
from sprigconfig import ConfigLoader, load_config

cfg = load_config(
    profile="prod",
    config_dir=Path("config"),
    schema=AppSchema,
)

# Equivalent loader API
cfg = ConfigLoader(
    config_dir=Path("config"),
    profile="prod",
    schema=AppSchema,
).load()
```

Validation runs after imports and the profile overlay are merged, but before
SprigConfig injects `app.profile`, `sprigconfig._meta`, and `LazySecret`
wrappers. Generated sections therefore do not belong in the schema unless they
already exist in the user's merged configuration.

## Validation behavior

The validator checks:

- required dataclass fields;
- unknown keys at every dataclass level;
- nested dataclasses;
- `Any`, unions such as `int | None`, lists, and dictionaries;
- strict runtime types, including treating `bool` as distinct from `int`.

Defaulted fields may be absent from configuration. Defaults are used only to
decide whether a field is required; validation does not instantiate the
dataclass or insert default values into the returned configuration.

## Errors

Failures raise `ConfigValidationError`, which is also a `ConfigLoadError`:

```python
from sprigconfig import ConfigValidationError

try:
    cfg = load_config(profile="prod", config_dir="config", schema=AppSchema)
except ConfigValidationError as error:
    print(error)
```

Diagnostics use dotted paths, for example:

```text
Missing required key 'database.host'.
Type mismatch at 'database.port': expected int, got str.
Unknown key 'database.driver'.
```

## Current scope

The initial validator does not enforce enum membership, numeric ranges,
patterns, tuples, sets, or arbitrary third-party model types. Unsupported
typing constructs fail validation instead of being silently accepted.
