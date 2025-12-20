---
layout: default
title: Configuration
---

# Configuration

This guide covers the core concepts and API for working with SprigConfig.

---

## The Config Object

When you load configuration, SprigConfig returns a `Config` object—an immutable-ish mapping wrapper that provides convenient access patterns.

```python
from sprigconfig import load_config

cfg = load_config(profile="dev")
```

### Dictionary-like access

Config objects support standard dictionary operations:

```python
# Direct key access
port = cfg["server"]["port"]

# Iteration
for key in cfg:
    print(key, cfg[key])

# Length
print(len(cfg))

# Key membership
if "server" in cfg:
    print("Server config found")
```

### Dotted-key access

For deeply nested values, use dotted-key notation:

```python
# These are equivalent
port = cfg["server"]["port"]
port = cfg["server.port"]

# With default value
port = cfg.get("server.port", 8080)

# Check existence
if "server.port" in cfg:
    print("Port configured")
```

### Nested Config objects

When you access a nested dictionary, it's automatically wrapped as a Config object:

```python
server = cfg["server"]  # Returns a Config object
print(server["port"])   # 8080
print(server.get("host", "localhost"))
```

---

## Loading Configuration

### Simple loading

```python
from sprigconfig import load_config

# Load with profile
cfg = load_config(profile="dev")

# Load with custom directory
cfg = load_config(profile="prod", config_dir=Path("/opt/myapp/config"))
```

### Using ConfigLoader

For more control, use `ConfigLoader` directly:

```python
from pathlib import Path
from sprigconfig import ConfigLoader

loader = ConfigLoader(
    config_dir=Path("config"),
    profile="dev",
    ext="yml"  # or "json", "toml"
)
cfg = loader.load()
```

### ConfigLoader parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `config_dir` | `Path` | Directory containing configuration files |
| `profile` | `str` | Active profile (dev, test, prod, etc.) |
| `ext` | `str` | File extension (yml, yaml, json, toml) |

---

## Configuration Formats

SprigConfig supports three configuration formats:

### YAML (default)

```yaml
# application.yml
server:
  port: 8080
  host: localhost
```

### JSON

```json
{
  "server": {
    "port": 8080,
    "host": "localhost"
  }
}
```

### TOML

```toml
[server]
port = 8080
host = "localhost"
```

### Selecting a format

The format is determined by:

1. **Explicit parameter:** `ConfigLoader(ext="json")`
2. **Environment variable:** `SPRIGCONFIG_FORMAT=json`
3. **Default:** `yml`

**Important:** All files in a single load must use the same format. You cannot mix YAML and JSON files.

---

## Environment Variable Expansion

Configuration values can reference environment variables using `${VAR}` syntax:

```yaml
database:
  host: ${DB_HOST}
  port: ${DB_PORT:5432}
  username: ${DB_USER:admin}
```

### Syntax

| Pattern | Behavior |
|---------|----------|
| `${VAR}` | Expands to value of VAR, or remains unexpanded if missing |
| `${VAR:default}` | Expands to value of VAR, or uses default if missing |

### When expansion happens

Environment variables are expanded at load time, before YAML/JSON/TOML parsing.

```bash
export DB_HOST=db.example.com
```

```python
cfg = load_config(profile="prod")
print(cfg["database.host"])  # db.example.com
print(cfg["database.port"])  # 5432 (default used)
```

---

## Metadata

Every loaded configuration includes metadata under `sprigconfig._meta`:

```python
cfg = load_config(profile="dev")

meta = cfg["sprigconfig"]["_meta"]
print(meta["profile"])       # dev
print(meta["sources"])       # List of loaded files
print(meta["import_trace"])  # Import graph details
```

### Metadata fields

| Field | Description |
|-------|-------------|
| `profile` | The active profile |
| `sources` | Ordered list of file paths that were loaded |
| `import_trace` | Detailed import graph with depth and order |

### Using metadata for debugging

```python
# See all files that contributed to this config
for source in cfg["sprigconfig._meta.sources"]:
    print(f"Loaded: {source}")

# Check which profile is active
if cfg["sprigconfig._meta.profile"] == "prod":
    print("Running in production mode")
```

---

## Serialization

### Converting to dictionary

```python
# Get plain dict (secrets redacted)
data = cfg.to_dict()

# Get plain dict with secrets revealed (unsafe!)
data = cfg.to_dict(reveal_secrets=True)
```

### Dumping to YAML/JSON

```python
# Dump to YAML string (secrets redacted)
yaml_str = cfg.dump()

# Dump to JSON string
json_str = cfg.dump(output_format="json")

# Write to file
cfg.dump(Path("config-snapshot.yml"))

# Dump with secrets (unsafe!)
cfg.dump(safe=False)
```

---

## ConfigSingleton

For applications that need global access to configuration, use `ConfigSingleton`:

```python
from sprigconfig import ConfigSingleton

# At application startup (once only)
ConfigSingleton.initialize(
    profile="prod",
    config_dir="config"
)

# From anywhere in your application
def get_database_config():
    cfg = ConfigSingleton.get()
    return {
        "host": cfg["database.host"],
        "port": cfg["database.port"],
    }
```

### Thread safety

`ConfigSingleton` is thread-safe. Multiple threads can call `get()` safely.

### Initialization rules

- `initialize()` must be called exactly once
- Calling `initialize()` twice raises an error
- `get()` before `initialize()` raises an error
- Use `_clear_all()` only in tests

---

## Error Handling

SprigConfig raises `ConfigLoadError` for configuration problems:

```python
from sprigconfig import load_config, ConfigLoadError

try:
    cfg = load_config(profile="prod")
except ConfigLoadError as e:
    print(f"Configuration error: {e}")
```

### Common error causes

| Error | Cause |
|-------|-------|
| Missing file | Required file (e.g., `application-prod.yml`) not found |
| Invalid YAML/JSON/TOML | Syntax error in configuration file |
| Circular import | Import chain creates a cycle |
| Missing secret key | `APP_SECRET_KEY` not set for encrypted values |
| Invalid secret key | Key is not a valid Fernet key |

---

## BOM Handling

SprigConfig automatically handles UTF-8 BOM (Byte Order Mark) in configuration files. Files created on Windows with BOM markers are read correctly without producing malformed keys.

This is handled transparently—you don't need to do anything special.

---

## Best Practices

### Keep base configuration complete

Your `application.yml` should contain all keys with sensible defaults. Profile overlays should only override what's different.

### Use dotted keys for deep access

```python
# Prefer this
port = cfg.get("server.database.connection.port", 5432)

# Over this
port = cfg.get("server", {}).get("database", {}).get("connection", {}).get("port", 5432)
```

### Check metadata in tests

```python
def test_production_config():
    cfg = load_config(profile="prod")
    assert cfg["sprigconfig._meta.profile"] == "prod"
    assert "application-prod.yml" in str(cfg["sprigconfig._meta.sources"])
```

### Don't store Config objects long-term

Load configuration once at startup and pass values to components, rather than passing the Config object around.

---

[← Back to Documentation](index.md)
