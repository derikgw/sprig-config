# sprigconfig/parsers/json_parser.md

## Overview

The `JsonParser` class provides JSON parsing for SprigConfig using Python's standard library `json` module. JSON offers strict syntax and wide interoperability.

## Implementation

```python
import json

class JsonParser:
    def parse(self, text: str):
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(str(e))
```

## Design Decisions

### Standard Library

Uses the stdlib `json` module rather than third-party alternatives:

- **Zero dependencies** - No additional packages required
- **Battle-tested** - Part of Python since 2.6
- **Consistent behavior** - Same across all Python installations

### Error Handling

JSON decode errors are converted to `ValueError` for consistent error handling:

```python
try:
    config = json_parser.parse(invalid_json)
except ValueError as e:
    print(f"Parse error: {e}")
```

## File Extensions

The JSON parser handles `.json` files:

```
config/
├── application.json
├── application-dev.json
└── application-prod.json
```

## JSON vs YAML

### Advantages of JSON

- Stricter syntax (no ambiguity)
- Native browser support
- Faster parsing
- Better tooling support

### Disadvantages of JSON

- No comments allowed
- More verbose (quotes required)
- No multiline strings
- No anchors/aliases

### When to Use JSON

- API-driven configuration
- Generated config files
- Strict schema validation needed
- Interoperability with non-Python systems

## Example Configuration

```json
{
  "server": {
    "host": "localhost",
    "port": 8080
  },
  "database": {
    "url": "postgresql://localhost:5432/mydb",
    "pool_size": 10
  },
  "logging": {
    "level": "INFO",
    "format": "%(levelname)s - %(message)s"
  }
}
```

## Type Mapping

| JSON Type | Python Type |
|-----------|-------------|
| object | dict |
| array | list |
| string | str |
| number (int) | int |
| number (float) | float |
| true/false | bool |
| null | None |

## Limitations

- No comments (use YAML if comments needed)
- Trailing commas not allowed
- Keys must be strings (quoted)
- No date/time native support

## Dependencies

- **None** - Uses Python stdlib `json` module
