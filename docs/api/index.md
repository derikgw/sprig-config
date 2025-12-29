# API Reference

Welcome to the SprigConfig API reference documentation. This section provides detailed information about all public classes, functions, and modules.

## Quick Links

- [Core API](core.md) - `load_config()`, `Config`, `ConfigLoader`
- [Secrets](secrets.md) - `LazySecret` for encrypted configuration
- [Utilities](utilities.md) - `deep_merge()`, `ConfigSingleton`
- [Exceptions](exceptions.md) - Error handling and custom exceptions

## Public API Overview

SprigConfig exposes a minimal, stable API surface designed for ease of use and backward compatibility.

### Essential Imports

```python
from sprigconfig import load_config, Config, ConfigLoader
from sprigconfig import ConfigLoadError
from sprigconfig.lazy_secret import LazySecret
```

### API Stability Guarantees

- **Public API** (documented here): Stable, follows semantic versioning
- **Internal modules** (not documented): May change without notice
- **Deprecations**: Announced one minor version in advance

## Common Patterns

### Basic Configuration Loading

```python
from sprigconfig import load_config

# Load with automatic profile detection
cfg = load_config()

# Load with explicit profile
cfg = load_config(profile="prod")

# Load from custom directory
cfg = load_config(config_dir="/path/to/config")
```

### Using ConfigLoader Directly

```python
from sprigconfig import ConfigLoader

loader = ConfigLoader(
    config_dir="./config",
    profile="dev"
)
cfg = loader.load()
```

### Accessing Configuration

```python
# Dict-like access
db_host = cfg["database"]["host"]

# Dotted-key access
db_host = cfg.get("database.host")

# With defaults
db_port = cfg.get("database.port", 5432)
```

### Working with Secrets

```python
from sprigconfig.lazy_secret import LazySecret

# Secrets are LazySecret objects until decrypted
db_password = cfg["database"]["password"]  # LazySecret
actual_password = db_password.get()  # Decrypted string
```

## Module Organization

SprigConfig's public API is intentionally minimal:

```
sprigconfig/
├── __init__.py           # Public API exports
├── config.py             # Config class (dict-like wrapper)
├── config_loader.py      # ConfigLoader (main loading logic)
├── config_singleton.py   # ConfigSingleton (global cache)
├── lazy_secret.py        # LazySecret (encrypted values)
├── deepmerge.py          # deep_merge utility
├── exceptions.py         # ConfigLoadError and subclasses
├── cli.py                # Command-line interface
└── parsers/              # Internal parsers (YAML, JSON, TOML)
```

**Note:** Only modules listed in `sprigconfig.__all__` are part of the public API.

## Type Hints

SprigConfig is fully type-annotated. Use type checkers like mypy:

```python
from sprigconfig import Config, load_config

cfg: Config = load_config(profile="dev")
```

## Next Steps

- Browse the [Core API](core.md) for main functionality
- Check [Secrets](secrets.md) for encrypted configuration
- See [Configuration Guide](../configuration.md) for usage patterns
- Review [Examples](https://gitlab.com/dgw_software/sprig-config/-/tree/main/sprig-config-module/examples) for real-world code
