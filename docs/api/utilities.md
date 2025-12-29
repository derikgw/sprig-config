# Utilities API

Advanced utilities for configuration management and merging.

## deep_merge()

A utility function for deeply merging nested dictionaries with override semantics.

::: sprigconfig.deepmerge.deep_merge
    options:
      show_root_heading: true
      show_source: true

**Example:**

```python
from sprigconfig import deep_merge

base = {
    "database": {
        "host": "localhost",
        "port": 5432,
        "pool_size": 10
    },
    "features": {
        "analytics": False
    }
}

override = {
    "database": {
        "port": 3306,  # Override
        "ssl": True    # Add new key
    },
    "features": {
        "analytics": True  # Override
    }
}

result = deep_merge(base, override)
# {
#     "database": {
#         "host": "localhost",      # From base
#         "port": 3306,             # Overridden
#         "pool_size": 10,          # From base
#         "ssl": True               # Added from override
#     },
#     "features": {
#         "analytics": True         # Overridden
#     }
# }
```

### Merge Semantics

- **Dictionaries**: Recursively merged (deep merge)
- **Lists**: Replaced entirely (not merged)
- **Scalars**: Override takes precedence
- **Type conflicts**: Override replaces base (e.g., dict → list)

### Advanced Usage

```python
# Merging multiple layers
layer1 = {"a": 1, "b": {"x": 1}}
layer2 = {"b": {"y": 2}}
layer3 = {"b": {"z": 3}, "c": 3}

result = deep_merge(layer1, layer2)
result = deep_merge(result, layer3)
# {"a": 1, "b": {"x": 1, "y": 2, "z": 3}, "c": 3}
```

### When to Use

`deep_merge()` is useful when:

- Building configuration programmatically
- Implementing custom config loaders
- Merging data from multiple sources
- Testing merge behavior

**Note:** SprigConfig uses `deep_merge()` internally for all configuration merging.

---

## ConfigSingleton

A thread-safe singleton for globally shared configuration across your application.

::: sprigconfig.ConfigSingleton
    options:
      show_root_heading: true
      show_source: true
      members:
        - get_instance
        - load
        - reload
        - clear
        - is_loaded

**Example:**

```python
from sprigconfig import ConfigSingleton

# Load configuration once
ConfigSingleton.load(profile="prod")

# Access from anywhere in your application
def my_function():
    cfg = ConfigSingleton.get_instance()
    db_host = cfg.get("database.host")
    return db_host

def another_function():
    cfg = ConfigSingleton.get_instance()
    # Same config instance, no reload
    return cfg.get("app.name")
```

### Thread Safety

`ConfigSingleton` is thread-safe and implements lazy initialization:

```python
import threading
from sprigconfig import ConfigSingleton

def worker():
    # Each thread gets the same config instance
    cfg = ConfigSingleton.get_instance()
    print(cfg.get("app.name"))

# Safe to call from multiple threads
threads = [threading.Thread(target=worker) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### Lifecycle Management

```python
from sprigconfig import ConfigSingleton

# Load configuration
ConfigSingleton.load(profile="dev")

# Check if loaded
if ConfigSingleton.is_loaded():
    cfg = ConfigSingleton.get_instance()

# Reload configuration (e.g., after config file changes)
ConfigSingleton.reload(profile="dev")

# Clear singleton (useful for testing)
ConfigSingleton.clear()
```

### Web Application Pattern

Common pattern for Flask/FastAPI applications:

```python
from flask import Flask
from sprigconfig import ConfigSingleton

def create_app():
    app = Flask(__name__)

    # Load config once at startup
    ConfigSingleton.load(profile="prod")

    # Use throughout request handlers
    @app.route("/api/info")
    def info():
        cfg = ConfigSingleton.get_instance()
        return {
            "app": cfg.get("app.name"),
            "version": cfg.get("app.version")
        }

    return app

app = create_app()
```

### Testing with ConfigSingleton

Clear the singleton between tests to avoid state leakage:

```python
import pytest
from sprigconfig import ConfigSingleton

@pytest.fixture(autouse=True)
def clear_config_singleton():
    """Clear singleton before each test."""
    ConfigSingleton.clear()
    yield
    ConfigSingleton.clear()

def test_my_feature():
    ConfigSingleton.load(profile="test")
    cfg = ConfigSingleton.get_instance()
    assert cfg.get("app.profile") == "test"
```

### When to Use ConfigSingleton

✅ **Good use cases:**
- Web applications (Flask, FastAPI, Django)
- Long-running services
- Applications with many modules
- Avoiding repeated file I/O

❌ **Avoid when:**
- Writing libraries (let consumers manage config)
- Need multiple configurations simultaneously
- Frequent config reloading required
- Testing with different configs in parallel

### Alternative: Direct load_config()

If you don't need global sharing:

```python
from sprigconfig import load_config

# Simple, explicit, no singleton
cfg = load_config(profile="dev")

# Pass config explicitly to functions
def my_function(cfg):
    return cfg.get("database.host")

result = my_function(cfg)
```

---

## Comparison: load_config() vs ConfigSingleton

| Feature | `load_config()` | `ConfigSingleton` |
|---------|-----------------|-------------------|
| **Use case** | Simple scripts, explicit config | Web apps, global sharing |
| **State** | Stateless, creates new `Config` | Singleton, cached globally |
| **Thread safety** | Each call is independent | Shared across threads |
| **Testing** | Easy to test with different configs | Needs cleanup between tests |
| **Overhead** | Reads files on each call | Reads once, caches forever |
| **Recommended for** | Libraries, scripts, tests | Applications, services |

---

## Examples

### Example 1: Manual Config Merging

```python
from sprigconfig import deep_merge

# Load multiple config sources
import yaml

with open("defaults.yml") as f:
    defaults = yaml.safe_load(f)

with open("overrides.yml") as f:
    overrides = yaml.safe_load(f)

# Merge manually
config = deep_merge(defaults, overrides)
```

### Example 2: Application-Wide Config

```python
# app/__init__.py
from sprigconfig import ConfigSingleton

def init_app():
    ConfigSingleton.load(profile="prod")
    print("Configuration loaded")

# app/database.py
from sprigconfig import ConfigSingleton

def get_db_connection():
    cfg = ConfigSingleton.get_instance()
    return connect(
        host=cfg.get("database.host"),
        port=cfg.get("database.port")
    )

# app/api.py
from sprigconfig import ConfigSingleton

def get_api_client():
    cfg = ConfigSingleton.get_instance()
    return APIClient(
        base_url=cfg.get("api.base_url"),
        api_key=cfg.get("api.key").get()
    )
```

### Example 3: Config Reload on Signal

```python
import signal
from sprigconfig import ConfigSingleton

def reload_config(signum, frame):
    print("Reloading configuration...")
    ConfigSingleton.reload()
    print("Configuration reloaded")

# Reload config on SIGHUP
signal.signal(signal.SIGHUP, reload_config)

# Initial load
ConfigSingleton.load(profile="prod")

# Send SIGHUP to reload: kill -HUP <pid>
```

---

## Related Documentation

- [Core API](core.md) - Main configuration loading functions
- [Configuration Guide](../configuration.md) - General configuration usage
- [Examples](https://gitlab.com/dgw_software/sprig-config/-/tree/main/sprig-config-module/examples) - Real-world code samples
