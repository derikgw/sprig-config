# sprigconfig/parsers/__init__.md

## Overview

The `parsers` package provides format-specific configuration file parsers for SprigConfig. Each parser implements a consistent interface for parsing text content into Python dictionaries.

## Supported Formats

| Format | Parser Class | File Extensions | Library |
|--------|--------------|-----------------|---------|
| YAML | `YamlParser` | `.yml`, `.yaml` | PyYAML |
| JSON | `JsonParser` | `.json` | stdlib `json` |
| TOML | `TomlParser` | `.toml` | stdlib `tomllib` |

## Architecture

### Parser Interface

All parsers implement the same simple interface:

```python
class Parser:
    def parse(self, text: str) -> dict:
        """
        Parse text content into a dictionary.

        Args:
            text: Raw file content as string

        Returns:
            Parsed configuration as dict

        Raises:
            ValueError: If parsing fails
        """
        ...
```

### Design Principles

1. **Parsing is a leaf concern** - Parsers only handle format conversion, not config semantics
2. **Consistent error handling** - All parsers raise `ValueError` for parse errors
3. **No behavior differences** - Same config structure produces same result across formats
4. **Stdlib preference** - Use Python stdlib where possible (JSON, TOML)

## Usage

Parsers are used internally by `ConfigLoader`. Direct usage:

```python
from sprigconfig.parsers import YamlParser, JsonParser, TomlParser

# YAML
yaml_parser = YamlParser()
config = yaml_parser.parse("server:\n  port: 8080")

# JSON
json_parser = JsonParser()
config = json_parser.parse('{"server": {"port": 8080}}')

# TOML
toml_parser = TomlParser()
config = toml_parser.parse("[server]\nport = 8080")
```

## Parser Selection

`ConfigLoader` selects the parser based on file extension:

```python
PARSER_REGISTRY = {
    ".yml": YamlParser,
    ".yaml": YamlParser,
    ".json": JsonParser,
    ".toml": TomlParser,
}
```

The `ext` parameter can override automatic detection:

```python
loader = ConfigLoader(config_dir=path, profile="dev", ext="json")
```

## Exports

```python
from .yaml_parser import YamlParser
from .json_parser import JsonParser
from .toml_parser import TomlParser

__all__ = ["YamlParser", "JsonParser", "TomlParser"]
```

## Future Considerations

- Parser registration API (Phase 6 roadmap)
- Custom format support via plugins
- Schema validation hooks
