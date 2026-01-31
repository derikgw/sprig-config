# sprigconfig/parsers/yaml_parser.md

## Overview

The `YamlParser` class provides YAML parsing for SprigConfig using PyYAML. YAML is the default and recommended configuration format.

## Implementation

```python
import yaml

class YamlParser:
    def parse(self, text: str):
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError as e:
            raise ValueError(str(e))
```

## Design Decisions

### Safe Loading

Uses `yaml.safe_load()` instead of `yaml.load()` to prevent arbitrary code execution. This is a security-critical choice:

- **safe_load**: Only loads basic Python types (dict, list, str, int, float, bool, None)
- **load**: Can instantiate arbitrary Python objects (security risk)

### Error Handling

YAML parsing errors are converted to `ValueError` for consistent error handling across all parsers:

```python
try:
    config = yaml_parser.parse(invalid_yaml)
except ValueError as e:
    print(f"Parse error: {e}")
```

## File Extensions

The YAML parser handles both `.yml` and `.yaml` extensions:

```
config/
├── application.yml       # Preferred
├── application.yaml      # Also supported
└── application-dev.yml
```

## YAML Features Supported

### Basic Types

```yaml
string: "hello"
integer: 42
float: 3.14
boolean: true
null_value: null
```

### Collections

```yaml
list:
  - item1
  - item2

dict:
  key1: value1
  key2: value2
```

### Multiline Strings

```yaml
# Literal block (preserves newlines)
literal: |
  Line 1
  Line 2

# Folded block (joins lines)
folded: >
  This is a long
  paragraph.
```

### Anchors and Aliases

```yaml
defaults: &defaults
  timeout: 30
  retries: 3

server:
  <<: *defaults
  host: localhost
```

## UTF-8 BOM Handling

Files are read with `utf-8-sig` encoding in `ConfigLoader`, which strips UTF-8 BOM markers automatically. This prevents issues like keys appearing as `ï»¿server` when files are created on Windows.

## Dependencies

- **PyYAML** (≥6.0.2) - Required dependency in `pyproject.toml`

## Security Notes

- Always uses `safe_load()` to prevent code injection
- No support for custom YAML tags or constructors
- Arbitrary Python object instantiation is blocked
