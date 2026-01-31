---
title: Getting Started
---

# Getting Started

This guide walks you through installing SprigConfig and loading your first configuration.

---

## Installation

Install SprigConfig from PyPI:

```bash
pip install sprig-config
```

Or with Poetry:

```bash
poetry add sprig-config
```

**Requirements:** Python 3.13 or later.

---

## Project Setup

Create a `config/` directory in your project root:

```
my-project/
├── config/
│   ├── application.yml
│   ├── application-dev.yml
│   ├── application-test.yml
│   └── application-prod.yml
├── src/
│   └── ...
└── pyproject.toml
```

---

## Your First Configuration

### Base configuration

Create `config/application.yml` with shared defaults:

```yaml
# config/application.yml
server:
  host: localhost
  port: 8080

database:
  pool_size: 5
  timeout: 30

logging:
  level: INFO
  format: "%(levelname)s - %(message)s"
```

### Development overlay

Create `config/application-dev.yml` for development overrides:

```yaml
# config/application-dev.yml
server:
  port: 9090

logging:
  level: DEBUG
```

### Production overlay

Create `config/application-prod.yml` for production:

```yaml
# config/application-prod.yml
server:
  host: 0.0.0.0

database:
  pool_size: 20

logging:
  level: INFO
```

---

## Loading Configuration

### Basic usage

```python
from sprigconfig import load_config

# Load with explicit profile
cfg = load_config(profile="dev")

# Access values
print(cfg["server"]["port"])      # 9090
print(cfg["server"]["host"])      # localhost
print(cfg["database"]["pool_size"])  # 5
```

### Dotted-key access

SprigConfig supports convenient dotted-key notation:

```python
# These are equivalent
port = cfg["server"]["port"]
port = cfg["server.port"]
port = cfg.get("server.port")

# With default value
port = cfg.get("server.port", 8080)
```

### Check if key exists

```python
if "server.port" in cfg:
    print("Port is configured")
```

---

## Profile Selection

Profiles are determined at runtime in this order:

1. **Explicit parameter:** `load_config(profile="prod")`
2. **Environment variable:** `APP_PROFILE=prod`
3. **pytest context:** Automatically uses `"test"`
4. **Default:** Falls back to `"dev"`

The active profile is always available in the config:

```python
print(cfg["app.profile"])  # dev, test, or prod
```

**Important:** Never set `app.profile` in your YAML files. SprigConfig ignores it with a warning.

---

## Configuration Directory

By default, SprigConfig looks for `config/` in your project root. You can customize this:

### Via parameter

```python
from pathlib import Path
cfg = load_config(profile="dev", config_dir=Path("/opt/myapp/config"))
```

### Via environment variable

```bash
export APP_CONFIG_DIR=/opt/myapp/config
```

### Via .env file

Create a `.env` file in your project root:

```
APP_CONFIG_DIR=/opt/myapp/config
APP_PROFILE=dev
```

---

## Using ConfigLoader (Modern API)

For more control, use the `ConfigLoader` class directly:

```python
from pathlib import Path
from sprigconfig import ConfigLoader

loader = ConfigLoader(
    config_dir=Path("config"),
    profile="dev"
)
cfg = loader.load()
```

---

## Using ConfigSingleton (Application Pattern)

For applications that need global access to configuration:

```python
from sprigconfig import ConfigSingleton

# Initialize once at startup
ConfigSingleton.initialize(profile="prod", config_dir="config")

# Access from anywhere in your application
cfg = ConfigSingleton.get()
print(cfg["database.pool_size"])
```

**Note:** `initialize()` can only be called once. Subsequent calls raise an error.

---

## Environment Variable Expansion

Configuration values can reference environment variables:

```yaml
# config/application.yml
database:
  host: ${DB_HOST}
  port: ${DB_PORT:5432}    # Default to 5432 if not set
  password: ${DB_PASSWORD}
```

```bash
export DB_HOST=db.example.com
export DB_PASSWORD=secret
```

```python
cfg = load_config(profile="prod")
print(cfg["database.host"])  # db.example.com
print(cfg["database.port"])  # 5432 (default)
```

---

## What's Next?

Now that you have basic configuration working:

- [Configuration](configuration.md) — Learn about the Config object and API
- [Merge Order](merge-order.md) — Understand how layering works
- [Profiles](profiles.md) — Deep dive into profile management
- [Imports](imports.md) — Modularize your configuration
- [Security](security.md) — Handle sensitive values securely
- [Dependency Injection](sprig-config-module/docs/configuration-injection.md) — Spring Boot-style `ConfigValue` and `@ConfigurationProperties`
- [Dynamic Instantiation](sprig-config-module/src/sprigconfig/instantiate.md) — Hydra-style `_target_` class instantiation

---

[← Back to Documentation](index.md)
