# Core API

The core API provides the primary interfaces for loading and accessing configuration.

## load_config()

The main entry point for loading configuration. This is a convenience function that creates a `ConfigLoader` instance and returns a `Config` object.

::: sprigconfig.load_config

**Example:**

```python
from sprigconfig import load_config

# Basic usage
cfg = load_config()

# With explicit profile
cfg = load_config(profile="prod")

# With custom config directory
cfg = load_config(config_dir="/etc/myapp/config")
```

---

## Config

A dict-like wrapper that provides convenient access to configuration values with support for dotted-key notation.

::: sprigconfig.Config
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - get
        - __getitem__
        - __setitem__
        - __contains__
        - keys
        - values
        - items
        - to_dict

**Example:**

```python
from sprigconfig import load_config

cfg = load_config()

# Dict-like access
db_host = cfg["database"]["host"]

# Dotted-key access
db_host = cfg.get("database.host")

# Default values
timeout = cfg.get("database.timeout", 30)

# Check if key exists
if "features.analytics" in cfg:
    print("Analytics configured")

# Iterate over keys
for key in cfg.keys():
    print(key)

# Convert to plain dict
plain_dict = cfg.to_dict()
```

---

## ConfigLoader

The primary configuration loading engine. Handles file discovery, parsing, merging, profile overlays, and imports.

::: sprigconfig.ConfigLoader
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - load
        - _resolve_profile
        - _resolve_config_dir

**Example:**

```python
from sprigconfig import ConfigLoader
from pathlib import Path

# Create loader with explicit settings
loader = ConfigLoader(
    config_dir=Path("./config"),
    profile="prod"
)

# Load configuration
cfg = loader.load()

# Access values
print(cfg.get("app.name"))
```

**Advanced Usage:**

```python
# Programmatic profile resolution
import os

profile = os.environ.get("DEPLOY_ENV", "dev")
loader = ConfigLoader(profile=profile)
cfg = loader.load()

# Custom config directory from environment
config_dir = os.environ.get("APP_CONFIG_DIR", "./config")
loader = ConfigLoader(config_dir=config_dir)
cfg = loader.load()
```

---

## Key Concepts

### Configuration Loading Flow

1. **Profile Resolution**: Determine active profile (explicit, `APP_PROFILE`, pytest context, or 'dev')
2. **Directory Resolution**: Locate config directory (explicit, `APP_CONFIG_DIR`, or './config')
3. **File Discovery**: Find `application.<ext>` and `application-<profile>.<ext>`
4. **Parsing**: Parse configuration files (YAML, JSON, or TOML)
5. **Merging**: Deep merge base + imports + profile + profile imports
6. **Processing**: Expand environment variables, create LazySecret objects
7. **Metadata**: Inject `sprigconfig._meta` with provenance information

### Profile Behavior

Profiles are **runtime-driven** and never read from configuration files:

- Explicit: `load_config(profile="prod")`
- Environment: `APP_PROFILE=prod`
- Pytest: Automatically uses "test"
- Default: "dev"

### File Formats

SprigConfig supports three configuration formats:

- **YAML** (`.yml`, `.yaml`) - Default, most common
- **JSON** (`.json`) - Structured data
- **TOML** (`.toml`) - Configuration-focused

**Important:** Use exactly one format per project. Mixed-format imports are not supported.

### Merge Semantics

Configuration is merged in this order (later overrides earlier):

1. `application.<ext>` (base)
2. Base imports
3. `application-<profile>.<ext>` (profile overlay)
4. Profile imports

This ensures profile-specific settings always have final say.

---

## Thread Safety

All core API components are thread-safe:

- `load_config()` can be called from multiple threads
- `Config` objects are safe for concurrent reads
- Use `ConfigSingleton` for shared configuration across threads

See [Utilities API](utilities.md#configsingleton) for thread-safe caching patterns.
