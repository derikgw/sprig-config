# sprigconfig/parsers/toml_parser.md

## Overview

The `TomlParser` class provides TOML parsing for SprigConfig using Python's standard library `tomllib` module (available since Python 3.11). TOML offers a clean, human-readable syntax with explicit typing.

## Implementation

```python
import tomllib

class TomlParser:
    def parse(self, text: str):
        try:
            return tomllib.loads(text)
        except tomllib.TOMLDecodeError as e:
            raise ValueError(str(e))
```

## Design Decisions

### Standard Library

Uses the stdlib `tomllib` module (Python 3.11+):

- **Zero dependencies** - No additional packages required
- **Official TOML support** - Part of Python since 3.11
- **Read-only by design** - `tomllib` only parses, doesn't write

### Error Handling

TOML decode errors are converted to `ValueError` for consistent error handling:

```python
try:
    config = toml_parser.parse(invalid_toml)
except ValueError as e:
    print(f"Parse error: {e}")
```

## File Extensions

The TOML parser handles `.toml` files:

```
config/
├── application.toml
├── application-dev.toml
└── application-prod.toml
```

## TOML vs YAML

### Advantages of TOML

- Explicit typing (strings must be quoted)
- Native datetime support
- Less ambiguous syntax
- Better for deeply nested config
- Comments supported

### Disadvantages of TOML

- More verbose for lists
- Less flexible than YAML
- No anchors/aliases

### When to Use TOML

- Python projects (pyproject.toml convention)
- Configuration with explicit types
- Datetime values needed
- Avoiding YAML's implicit typing surprises

## Example Configuration

```toml
[server]
host = "localhost"
port = 8080

[database]
url = "postgresql://localhost:5432/mydb"
pool_size = 10
timeout = 30.0

[database.connection]
min_size = 5
max_size = 20

[logging]
level = "INFO"
format = "%(levelname)s - %(message)s"

# Arrays
[features]
enabled = ["auth", "caching", "metrics"]
```

## Type Mapping

| TOML Type | Python Type |
|-----------|-------------|
| Table | dict |
| Array | list |
| String | str |
| Integer | int |
| Float | float |
| Boolean | bool |
| Offset Date-Time | datetime.datetime |
| Local Date-Time | datetime.datetime |
| Local Date | datetime.date |
| Local Time | datetime.time |

## TOML-Specific Features

### Inline Tables

```toml
server = { host = "localhost", port = 8080 }
```

### Array of Tables

```toml
[[servers]]
name = "alpha"
ip = "10.0.0.1"

[[servers]]
name = "beta"
ip = "10.0.0.2"
```

### Multiline Strings

```toml
# Basic multiline
description = """
This is a long
description.
"""

# Literal (preserves whitespace)
regex = '''\\d{3}-\\d{4}'''
```

### Native Datetime

```toml
created_at = 2024-01-15T10:30:00Z
date_only = 2024-01-15
time_only = 10:30:00
```

## Limitations

- Read-only (`tomllib` doesn't write TOML)
- Python 3.11+ required (stdlib)
- No anchors/aliases like YAML

## Dependencies

- **None** - Uses Python stdlib `tomllib` module
- **Requires Python 3.11+** (SprigConfig requires 3.13+ anyway)
