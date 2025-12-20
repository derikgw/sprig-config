---
layout: default
title: Profiles
---

# Profiles

Profiles allow you to maintain environment-specific configuration without code changes. SprigConfig's profile system is **runtime-driven**—profiles are never read from configuration files.

---

## How Profiles Work

A profile determines which overlay file is loaded on top of the base configuration:

| Profile | Overlay File |
|---------|--------------|
| `dev` | `application-dev.yml` |
| `test` | `application-test.yml` |
| `prod` | `application-prod.yml` |
| `staging` | `application-staging.yml` |
| `<custom>` | `application-<custom>.yml` |

The base `application.yml` is always loaded first, then the profile overlay is merged on top.

---

## Profile Selection

Profiles are determined at runtime in this order:

### 1. Explicit parameter (highest priority)

```python
cfg = load_config(profile="prod")
```

### 2. Environment variable

```bash
export APP_PROFILE=prod
```

```python
cfg = load_config()  # Uses "prod" from environment
```

### 3. pytest context

When running under pytest, SprigConfig automatically uses the `test` profile:

```python
# In test files, profile defaults to "test"
def test_something():
    cfg = load_config()  # Uses "test" profile
    assert cfg["app.profile"] == "test"
```

### 4. Default

If nothing else is specified, SprigConfig uses `dev`.

---

## Profile Injection

The active profile is always injected into the final configuration at `app.profile`:

```python
cfg = load_config(profile="prod")
print(cfg["app.profile"])  # prod
```

This allows your application to know which profile is active at runtime.

### Never set app.profile in files

**Important:** Do not set `app.profile` in your YAML files. SprigConfig ignores it with a warning:

```yaml
# DON'T DO THIS - will be ignored
app:
  profile: dev
```

The runtime always determines the profile, ensuring consistency between what's loaded and what's reported.

---

## Standard Profiles

While you can use any profile name, these are the conventional profiles:

### `dev` — Development

Local development environment with debug settings:

```yaml
# application-dev.yml
server:
  port: 9090

logging:
  level: DEBUG

features:
  hot_reload: true
  debug_toolbar: true
```

### `test` — Testing

Isolated configuration for automated tests:

```yaml
# application-test.yml
database:
  url: sqlite:///:memory:

logging:
  level: WARNING

features:
  email: false  # Don't send real emails in tests
```

### `prod` — Production

Production-hardened configuration:

```yaml
# application-prod.yml
server:
  host: 0.0.0.0

database:
  pool_size: 20
  ssl: true

logging:
  level: INFO

features:
  debug_toolbar: false
```

---

## Production Guardrails

SprigConfig includes safety checks for production:

### Required production file

When using the `prod` profile, `application-prod.yml` must exist. This prevents accidentally running with dev settings in production.

```python
# Raises ConfigLoadError if application-prod.yml is missing
cfg = load_config(profile="prod")
```

### DEBUG logging protection

DEBUG logging in production is blocked by default:

```yaml
# application-prod.yml
logging:
  level: DEBUG  # Blocked unless allow_debug_in_prod is set
```

To allow DEBUG in production (not recommended):

```yaml
# application-prod.yml
allow_debug_in_prod: true
logging:
  level: DEBUG
```

### Default logging level

If no logging level is specified in production, SprigConfig defaults to `INFO`.

---

## Custom Profiles

You can create profiles for any environment:

```yaml
# application-staging.yml
database:
  host: staging-db.example.com

# application-qa.yml
features:
  test_accounts: true

# application-local.yml
server:
  port: 3000
```

Load them by name:

```python
cfg = load_config(profile="staging")
cfg = load_config(profile="qa")
cfg = load_config(profile="local")
```

---

## Profile-Specific Imports

Each profile can have its own imports:

```yaml
# application.yml
server:
  port: 8080
imports:
  - common/logging.yml
  - common/security.yml

# application-dev.yml
imports:
  - dev/mock-services.yml
  - dev/debug-settings.yml

# application-prod.yml
imports:
  - prod/monitoring.yml
  - prod/security-hardening.yml
```

Import order:
1. Base file
2. Base imports
3. Profile file
4. Profile imports

See [Merge Order](merge-order.md) for details.

---

## Checking Profile at Runtime

Use the injected `app.profile` to make runtime decisions:

```python
cfg = load_config()

if cfg["app.profile"] == "prod":
    # Production-specific initialization
    setup_monitoring()
    enable_rate_limiting()
elif cfg["app.profile"] == "dev":
    # Development helpers
    enable_debug_toolbar()
```

Or access from metadata:

```python
profile = cfg["sprigconfig._meta.profile"]
```

---

## Testing with Profiles

### Explicit test profile

```python
def test_production_config():
    cfg = load_config(profile="prod", config_dir=Path("tests/config"))
    assert cfg["database.ssl"] == True
```

### Using pytest fixtures

```python
import pytest
from sprigconfig import load_config

@pytest.fixture
def prod_config():
    return load_config(profile="prod")

def test_pool_size(prod_config):
    assert prod_config["database.pool_size"] >= 10
```

### Environment variable in tests

```python
import os

def test_with_custom_profile(monkeypatch):
    monkeypatch.setenv("APP_PROFILE", "staging")
    cfg = load_config()
    assert cfg["app.profile"] == "staging"
```

---

## Best Practices

### Keep base complete

Your `application.yml` should define all keys with sensible defaults. Profiles should only override what's different.

```yaml
# application.yml - complete defaults
server:
  host: localhost
  port: 8080
  timeout: 30
  max_connections: 100

# application-prod.yml - only overrides
server:
  host: 0.0.0.0
  max_connections: 1000
```

### Don't duplicate across profiles

If a value is the same in dev and test, keep it in the base file.

### Use environment variables for secrets

Don't hardcode credentials in profile files:

```yaml
# application-prod.yml
database:
  password: ${DB_PASSWORD}  # Or use ENC() for encrypted values
```

### Test all profiles

Ensure each profile loads successfully:

```python
@pytest.mark.parametrize("profile", ["dev", "test", "prod"])
def test_profile_loads(profile):
    cfg = load_config(profile=profile)
    assert cfg["app.profile"] == profile
```

---

[← Back to Documentation](index.md)
