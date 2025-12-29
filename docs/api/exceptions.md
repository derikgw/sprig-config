# Exceptions API

Error handling and exception classes for SprigConfig.

## ConfigLoadError

Base exception for all configuration loading errors.

::: sprigconfig.exceptions.ConfigLoadError
    options:
      show_root_heading: true
      show_source: true

**Example:**

```python
from sprigconfig import load_config, ConfigLoadError

try:
    cfg = load_config(profile="prod")
except ConfigLoadError as e:
    print(f"Failed to load configuration: {e}")
    # Handle error (use defaults, exit, etc.)
```

---

## Exception Hierarchy

SprigConfig uses a simple exception hierarchy:

```
Exception
└── ConfigLoadError (base for all config errors)
```

All configuration-related errors inherit from `ConfigLoadError`, making it easy to catch any config-related issue:

```python
try:
    cfg = load_config()
except ConfigLoadError:
    # Catches all config-related errors
    handle_config_error()
```

---

## Common Error Scenarios

### 1. Missing Configuration File

**Scenario:** Required configuration file not found

```python
# config/application.yml does not exist
from sprigconfig import load_config, ConfigLoadError

try:
    cfg = load_config()
except ConfigLoadError as e:
    print(f"Error: {e}")
    # "Configuration file not found: config/application.yml"
```

**Solutions:**
- Create the missing file
- Check `config_dir` parameter
- Set `APP_CONFIG_DIR` environment variable

### 2. Production Profile Missing

**Scenario:** Production mode requires `application-prod.yml` to exist

```python
from sprigconfig import load_config, ConfigLoadError

try:
    cfg = load_config(profile="prod")
except ConfigLoadError as e:
    print(f"Error: {e}")
    # "Production profile requires application-prod.yml"
```

**Solution:**
- Create `config/application-prod.yml`
- This is a safety feature to prevent accidental production deployments with dev config

### 3. Invalid YAML/JSON/TOML Syntax

**Scenario:** Configuration file has syntax errors

```yaml
# config/application.yml (invalid)
database:
  host: localhost
  port: [invalid syntax here
```

```python
from sprigconfig import load_config, ConfigLoadError

try:
    cfg = load_config()
except ConfigLoadError as e:
    print(f"Parse error: {e}")
```

**Solutions:**
- Validate YAML/JSON/TOML syntax
- Use a linter or validator
- Check for common issues (indentation, quotes, commas)

### 4. Circular Import Detected

**Scenario:** Configuration files import each other in a loop

```yaml
# config/application.yml
imports:
  - database.yml

# config/database.yml
imports:
  - application.yml  # Circular!
```

```python
from sprigconfig import load_config, ConfigLoadError

try:
    cfg = load_config()
except ConfigLoadError as e:
    print(f"Error: {e}")
    # "Circular import detected: application.yml -> database.yml -> application.yml"
```

**Solution:**
- Remove circular imports
- Restructure your configuration files
- Use a hierarchical import structure

### 5. Missing Encryption Key

**Scenario:** Configuration has encrypted secrets but `APP_SECRET_KEY` not set

```yaml
# config/application.yml
database:
  password: ENC(gAAAAAB...)  # Encrypted secret
```

```python
from sprigconfig import load_config

cfg = load_config()

# Later, when trying to decrypt
try:
    password = cfg["database"]["password"].get()
except Exception as e:
    print(f"Decryption error: {e}")
    # "No encryption key available"
```

**Solutions:**
- Set `APP_SECRET_KEY` environment variable
- Use `LazySecret.set_global_key_provider()`
- Pass key explicitly: `secret.get(key="your-key")`

### 6. Invalid Configuration Directory

**Scenario:** Specified config directory doesn't exist

```python
from sprigconfig import load_config, ConfigLoadError

try:
    cfg = load_config(config_dir="/nonexistent/path")
except ConfigLoadError as e:
    print(f"Error: {e}")
    # "Configuration directory not found: /nonexistent/path"
```

**Solution:**
- Verify the path exists
- Check file permissions
- Use absolute paths to avoid ambiguity

---

## Error Handling Patterns

### Pattern 1: Graceful Degradation

```python
from sprigconfig import load_config, ConfigLoadError

def get_config():
    """Load config with fallback to defaults."""
    try:
        return load_config()
    except ConfigLoadError as e:
        print(f"Warning: Using default config due to: {e}")
        return {
            "database": {"host": "localhost", "port": 5432},
            "app": {"debug": False}
        }

cfg = get_config()
```

### Pattern 2: Fail Fast

```python
from sprigconfig import load_config, ConfigLoadError
import sys

try:
    cfg = load_config(profile="prod")
except ConfigLoadError as e:
    print(f"FATAL: Cannot load configuration: {e}", file=sys.stderr)
    sys.exit(1)

# Continue with valid config
```

### Pattern 3: Detailed Error Logging

```python
import logging
from sprigconfig import load_config, ConfigLoadError

logger = logging.getLogger(__name__)

try:
    cfg = load_config()
except ConfigLoadError as e:
    logger.error(
        "Configuration load failed",
        exc_info=True,
        extra={
            "error": str(e),
            "profile": "dev",
            "config_dir": "./config"
        }
    )
    raise
```

### Pattern 4: Retry with Fallback

```python
from sprigconfig import load_config, ConfigLoadError
import os

def load_with_fallback():
    """Try loading from primary location, then fallback."""
    try:
        return load_config(config_dir="/etc/myapp/config")
    except ConfigLoadError:
        # Try fallback location
        try:
            return load_config(config_dir="./config")
        except ConfigLoadError as e:
            raise ConfigLoadError(
                f"Failed to load config from primary and fallback locations: {e}"
            )

cfg = load_with_fallback()
```

---

## Validation and Error Prevention

### Pre-flight Checks

```python
from pathlib import Path
from sprigconfig import load_config, ConfigLoadError

def validate_config_setup(profile="dev"):
    """Validate configuration before loading."""
    config_dir = Path("./config")

    # Check directory exists
    if not config_dir.exists():
        raise ConfigLoadError(f"Config directory not found: {config_dir}")

    # Check base file exists
    base_file = config_dir / "application.yml"
    if not base_file.exists():
        raise ConfigLoadError(f"Base config not found: {base_file}")

    # Check profile file exists (for prod)
    if profile == "prod":
        profile_file = config_dir / f"application-{profile}.yml"
        if not profile_file.exists():
            raise ConfigLoadError(f"Profile config not found: {profile_file}")

    return True

# Validate before loading
validate_config_setup(profile="prod")
cfg = load_config(profile="prod")
```

### Custom Validation

```python
from sprigconfig import load_config, ConfigLoadError

def load_and_validate():
    """Load config and validate required keys."""
    cfg = load_config()

    # Validate required keys
    required_keys = [
        "database.host",
        "database.port",
        "app.name"
    ]

    for key in required_keys:
        if key not in cfg:
            raise ConfigLoadError(f"Required configuration key missing: {key}")

    # Validate value types
    if not isinstance(cfg.get("database.port"), int):
        raise ConfigLoadError("database.port must be an integer")

    return cfg

cfg = load_and_validate()
```

---

## Debugging Configuration Errors

### Enable Debug Logging

```python
import logging
from sprigconfig import load_config

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Load config (will show detailed debug info)
cfg = load_config()
```

### Use CLI for Inspection

```bash
# Dump configuration to see what's loaded
sprigconfig dump --profile dev

# Validate configuration syntax
sprigconfig dump --profile prod --format yaml
```

### Check Configuration Files

```python
import yaml
from pathlib import Path

# Manually validate YAML syntax
config_file = Path("config/application.yml")
try:
    with open(config_file) as f:
        data = yaml.safe_load(f)
    print(f"Valid YAML: {config_file}")
except yaml.YAMLError as e:
    print(f"Invalid YAML: {e}")
```

---

## Error Messages

SprigConfig provides clear, actionable error messages:

| Error | Message | Solution |
|-------|---------|----------|
| Missing file | `Configuration file not found: config/application.yml` | Create the file or check path |
| Parse error | `Failed to parse config/application.yml: invalid syntax` | Fix YAML/JSON/TOML syntax |
| Circular import | `Circular import detected: a.yml -> b.yml -> a.yml` | Remove circular dependency |
| Production guard | `Production profile requires application-prod.yml` | Create prod config file |
| Missing key | `Required key not found: database.host` | Add missing configuration |

---

## Best Practices

1. **Always catch ConfigLoadError** - Don't let config errors crash silently
2. **Log detailed errors** - Include context (profile, paths) in error logs
3. **Validate early** - Check config at startup, not during requests
4. **Provide defaults** - Have sensible fallbacks for non-critical config
5. **Test error paths** - Write tests for config loading failures
6. **Document required config** - Make it clear what config is needed

---

## Related Documentation

- [Core API](core.md) - Main configuration loading
- [Configuration Guide](../configuration.md) - General usage patterns
- [FAQ](../faq.md) - Common questions and troubleshooting
