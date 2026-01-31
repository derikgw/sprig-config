---
title: FAQ
---

# Frequently Asked Questions

Common questions about SprigConfig, organized by topic.

---

## General

### What is SprigConfig?

SprigConfig is a lightweight, production-grade configuration system for Python applications. It brings Spring Boot-style configuration management to Python with layered YAML loading, profile overlays, recursive imports, secure secret handling, and complete provenance tracking.

### Why not just use environment variables?

Environment variables are great for deployment secrets and simple values, but they don't handle:
- Hierarchical configuration
- Default values with environment-specific overrides
- Configuration validation and debugging
- Provenance tracking (knowing where values came from)

SprigConfig works *with* environment variables (`${VAR}` expansion) while providing structure for complex configuration.

### Why not use a different library like Dynaconf or python-dotenv?

SprigConfig has a specific philosophy:
- **Deterministic behavior** — Same inputs always produce same output
- **Runtime-driven profiles** — Profiles never come from files
- **Complete provenance** — Know where every value originated
- **Security first** — Secrets are encrypted and lazy-decrypted

If these principles align with your needs, SprigConfig is a good fit. Other libraries may be better for different use cases.

### What Python versions are supported?

SprigConfig requires **Python 3.13 or later**.

---

## Profiles

### Why can't I set the profile in YAML files?

This is a core design principle. If profiles came from files, you'd have circular logic:
1. Which file determines the profile?
2. That file might be profile-specific!

Runtime-driven profiles ensure:
- Clear precedence (explicit → env var → pytest → default)
- No ambiguity about which profile is active
- Profiles can't accidentally override themselves

### How do I know which profile is active?

The active profile is always available at `app.profile`:

```python
cfg = load_config()
print(cfg["app.profile"])  # dev, test, or prod
```

Or in metadata:
```python
print(cfg["sprigconfig._meta.profile"])
```

### Can I use custom profile names?

Yes. Use any name you want:

```python
cfg = load_config(profile="staging")
cfg = load_config(profile="qa")
cfg = load_config(profile="local-docker")
```

Just create the corresponding overlay file (e.g., `application-staging.yml`).

### Why does pytest automatically use the "test" profile?

SprigConfig detects pytest execution and defaults to `test` profile. This prevents accidentally running tests with production settings.

Override if needed:
```python
cfg = load_config(profile="dev")  # Explicit override
```

---

## Configuration Files

### What file formats are supported?

- **YAML** (`.yml`, `.yaml`) — Default and recommended
- **JSON** (`.json`) — Strict, portable
- **TOML** (`.toml`) — Python 3.11+ stdlib

### Can I mix formats (e.g., YAML base with JSON overlay)?

No. All files in a single configuration load must use the same format. This is intentional—mixing formats would introduce ambiguity in merge semantics.

### Why isn't INI/Properties format supported?

Flat formats require inventing behavior for:
- Dot-splitting keys into hierarchy
- List coercion
- Type inference

This invented behavior would violate SprigConfig's principle of explicit, predictable configuration. See [Philosophy](philosophy.md) for details.

### How do I switch between formats?

```python
# Via parameter
loader = ConfigLoader(config_dir=Path("config"), profile="dev", ext="json")

# Via environment variable
export SPRIGCONFIG_FORMAT=json
```

---

## Merging

### Why do lists replace instead of append?

List appending creates ambiguity:
- What if you want to remove items?
- What's the order of appended items?
- How do you clear a list?

Replacement is explicit: you see exactly what the final list contains. If you want all items from base plus overlay, include them all in the overlay.

### How do I debug merge issues?

1. **Use the CLI:**
   ```bash
   sprigconfig dump --config-dir=config --profile=dev
   ```

2. **Check metadata:**
   ```python
   for source in cfg["sprigconfig._meta.sources"]:
       print(f"Loaded: {source}")
   ```

3. **Enable logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### What are "collision warnings"?

SprigConfig warns when an overlay might unintentionally lose keys. For example, if base has five keys and overlay mentions two, you'll see a warning.

Suppress if intentional:
```yaml
suppress_config_merge_warnings: true
```

---

## Imports

### Can imports create circular references?

No. SprigConfig detects cycles and raises `ConfigLoadError` with a clear message showing the cycle path.

### Can I import from parent directories?

No. Imports cannot escape the configuration directory. Path traversal like `../secrets.yml` is blocked for security.

### What's the difference between root and positional imports?

**Root imports** merge at the configuration root:
```yaml
imports:
  - database.yml  # Merges at root level
```

**Positional imports** merge at their location:
```yaml
database:
  imports:
    - connection.yml  # Merges under database:
```

---

## Secrets

### How secure is the encryption?

SprigConfig uses **Fernet encryption** from the `cryptography` library. Fernet provides:
- AES-128-CBC encryption
- HMAC-SHA256 authentication
- Timestamp validation

This is industry-standard symmetric encryption suitable for configuration secrets.

### What happens if I lose the encryption key?

Encrypted values cannot be recovered without the key. This is by design—there's no backdoor.

Best practices:
- Store keys in secret managers with backup
- Document key locations
- Test key recovery procedures

### Can I use different keys for different environments?

Yes, and you should. Generate a separate key for each environment to limit blast radius if a key is compromised.

### Why are secrets "lazy"?

Lazy decryption means:
- Secrets stay encrypted in memory until needed
- You control when decryption happens
- Logging configuration won't accidentally expose secrets
- Failed decryption is caught at point of use

---

## Performance

### Is SprigConfig slow?

Configuration is typically loaded once at application startup. SprigConfig's loading time is negligible for most applications.

If you're loading configuration in a hot path, use `ConfigSingleton` to load once and reuse.

### Does SprigConfig cache configuration?

`ConfigSingleton` caches the loaded configuration. Direct `load_config()` calls load fresh each time.

### Is ConfigSingleton thread-safe?

Yes. `ConfigSingleton` uses locking to ensure thread-safe initialization and access.

---

## Troubleshooting

### "ConfigLoadError: Profile file not found"

The profile overlay file doesn't exist:
```
application-staging.yml not found
```

Either create the file or use a different profile.

### "ConfigLoadError: No Fernet key available"

Set the encryption key before loading:
```bash
export APP_SECRET_KEY="your-key"
```

Or in code:
```python
from sprigconfig.lazy_secret import set_global_key
set_global_key("your-key")
```

### "ConfigLoadError: Circular import detected"

Your imports form a cycle. Check the error message for the cycle path and break it.

### "app.profile in YAML is ignored"

This is expected behavior. Remove `app.profile` from your YAML files—runtime determines the profile.

### Windows BOM characters in keys

SprigConfig handles this automatically. Files are read with `utf-8-sig` encoding which strips BOM markers.

---

## Dependency Injection

### What are ConfigValue, @ConfigurationProperties, and @config_inject?

SprigConfig provides three Spring Boot-style dependency injection patterns:

- **`ConfigValue`** — Field-level descriptor for lazy config binding with type conversion
- **`@ConfigurationProperties`** — Class-level decorator for auto-binding config sections
- **`@config_inject`** — Function parameter injection decorator with override support

```python
from sprigconfig import ConfigValue, ConfigurationProperties, config_inject

class MyService:
    db_url: str = ConfigValue("database.url")
    db_port: int = ConfigValue("database.port", default=5432)

@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    url: str
    port: int
```

### What is `_target_` and how does `instantiate()` work?

SprigConfig supports Hydra-style dynamic class instantiation from configuration:

```yaml
database:
  _target_: app.adapters.PostgresAdapter
  host: localhost
  port: 5432
```

```python
from sprigconfig import ConfigSingleton, instantiate

cfg = ConfigSingleton.get()
db = instantiate(cfg.database)  # Returns PostgresAdapter instance
```

This enables hexagonal architecture patterns where adapters are swapped via configuration.

---

## Integration

### Can I use SprigConfig with Pydantic?

Yes. Load configuration, then validate with Pydantic:

```python
from pydantic import BaseModel
from sprigconfig import load_config

class DatabaseConfig(BaseModel):
    host: str
    port: int
    pool_size: int

cfg = load_config(profile="prod")
db_config = DatabaseConfig(**cfg["database"])
```

### Can I use SprigConfig with FastAPI?

Yes:

```python
from fastapi import FastAPI
from sprigconfig import ConfigSingleton

ConfigSingleton.initialize(profile="prod", config_dir="config")

app = FastAPI()

@app.get("/config")
def get_config():
    cfg = ConfigSingleton.get()
    return {"port": cfg["server.port"]}
```

### Can I use SprigConfig with Django?

Yes, in `settings.py`:

```python
from sprigconfig import load_config

cfg = load_config(profile=os.getenv("DJANGO_ENV", "dev"))

DEBUG = cfg.get("django.debug", False)
DATABASES = {
    "default": {
        "HOST": cfg["database.host"],
        "PORT": cfg["database.port"],
    }
}
```

---

## Contributing

### How do I report bugs?

Open an issue at [GitLab](https://gitlab.com/dgw_software/sprig-config/-/issues) with:
- What you expected
- What happened
- Relevant configuration (redacted if needed)
- Python version

### Can I add support for new formats?

Format support may be considered if:
- There's demonstrated demand
- The format natively expresses hierarchy
- Semantics are explicit and documented

See [CONTRIBUTING.md](https://gitlab.com/dgw_software/sprig-config/-/blob/main/sprig-config-module/CONTRIBUTING.md) for guidelines.

---

[← Back to Documentation](index.md)
