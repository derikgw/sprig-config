# Configuration Injection Guide

## Overview

SprigConfig now supports Spring Boot-style dependency injection for cleaner, more declarative code. Instead of explicitly calling `Config.get()` everywhere, you can use annotations to automatically bind configuration values to:

- **Class fields** (via `ConfigValue` descriptor)
- **Entire classes** (via `@ConfigurationProperties` decorator)
- **Function parameters** (via `@config_inject` decorator)

All three patterns work alongside the traditional `Config.get()` approach - you can mix and match as needed.

## Quick Start

### Traditional Approach (Still Supported)

```python
from sprigconfig import ConfigSingleton

# Initialize at startup
ConfigSingleton.initialize(profile="dev", config_dir="./config")

# Use throughout your app
cfg = ConfigSingleton.get()
db_url = cfg.get("database.url")
db_port = cfg.get("database.port", 5432)
api_key = cfg.get("api.key").get()  # LazySecret
```

### New Approach (Dependency Injection)

```python
from sprigconfig import ConfigSingleton, ConfigValue, ConfigurationProperties

# Initialize at startup (same as before)
ConfigSingleton.initialize(profile="dev", config_dir="./config")

# Pattern 1: Field-level binding
class MyService:
    db_url: str = ConfigValue("database.url")
    db_port: int = ConfigValue("database.port", default=5432)
    api_key: str = ConfigValue("api.key", decrypt=True)

service = MyService()
print(service.db_url)  # "postgresql://localhost/mydb"

# Pattern 2: Class-level binding
@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    url: str
    port: int
    username: str

db = DatabaseConfig()
print(db.url)  # "postgresql://localhost/mydb"
```

---

## Pattern 1: ConfigValue (Field-Level Binding)

### Basic Usage

Use `ConfigValue` as a class attribute descriptor to bind individual config values:

```python
from sprigconfig import ConfigValue

class EmailService:
    smtp_host: str = ConfigValue("email.smtp.host")
    smtp_port: int = ConfigValue("email.smtp.port")
    from_address: str = ConfigValue("email.from", default="noreply@example.com")

service = EmailService()
print(service.smtp_host)  # Resolved from config
print(service.smtp_port)  # Resolved from config
print(service.from_address)  # Uses default if not in config
```

**Configuration file (application.yml):**
```yaml
email:
  smtp:
    host: smtp.gmail.com
    port: 587
```

### Type Conversion

ConfigValue automatically converts YAML values to Python types based on type hints:

```python
class AppConfig:
    # String values
    app_name: str = ConfigValue("app.name")  # YAML: "MyApp" → Python: "MyApp"

    # Numeric values
    port: int = ConfigValue("app.port")       # YAML: "8080" → Python: 8080
    timeout: float = ConfigValue("app.timeout")  # YAML: "30.5" → Python: 30.5

    # Boolean values
    debug: bool = ConfigValue("app.debug")    # YAML: "true" → Python: True

    # Collections (no conversion)
    tags: list = ConfigValue("app.tags")      # YAML: [a, b] → Python: ["a", "b"]
    metadata: dict = ConfigValue("app.metadata")  # YAML: {k: v} → Python: {"k": "v"}
```

**Supported boolean strings**: `"true"`, `"True"`, `"TRUE"`, `"1"`, `"yes"`, `"on"` → `True`

All other strings → `False`

### Default Values

Provide defaults for optional configuration:

```python
class ServiceConfig:
    # Required (error if missing)
    api_url: str = ConfigValue("service.api.url")

    # Optional with default
    timeout: int = ConfigValue("service.timeout", default=30)
    retries: int = ConfigValue("service.retries", default=3)
    cache_enabled: bool = ConfigValue("service.cache.enabled", default=False)
```

### LazySecret Handling

ConfigValue supports two modes for encrypted secrets:

#### Mode 1: Encrypted (decrypt=False, default)

Secret stays encrypted in memory. You must call `.get()` to decrypt:

```python
class APIClient:
    # Secret stays encrypted until you explicitly decrypt it
    api_key: str = ConfigValue("api.secret_key", decrypt=False)

    def make_request(self):
        # Decrypt only when needed
        key = self.api_key.get()
        return requests.get(url, headers={"Authorization": f"Bearer {key}"})
```

**Best for:** Rarely-accessed secrets (emergency keys, admin passwords)

#### Mode 2: Auto-Decrypt (decrypt=True)

Secret auto-decrypts at binding time (plaintext in memory):

```python
class DatabaseService:
    # Secret auto-decrypts immediately
    db_password: str = ConfigValue("database.password", decrypt=True)

    def connect(self):
        # Already decrypted, use directly
        return connect(host, user, self.db_password)
```

**Best for:** Frequently-used secrets (database passwords, API keys)

**Configuration file:**
```yaml
database:
  password: ENC(gAAAAABh...)  # Encrypted with Fernet
api:
  secret_key: ENC(gAAAAABi...)
```

**Security Recommendation:** Default to `decrypt=False` for maximum security. Only use `decrypt=True` for secrets accessed frequently in hot code paths.

### Lazy Resolution & Refresh

ConfigValue resolves from the current singleton on **every access** (no caching):

```python
class Service:
    timeout: int = ConfigValue("service.timeout")

# In tests
ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
service = Service()
print(service.timeout)  # 30 (from dev config)

# Reload singleton (test-only)
from tests.utils.config_test_utils import reload_for_testing
reload_for_testing(profile="prod", config_dir=config_dir)

print(service.timeout)  # 60 (from prod config) - auto-refreshed!
```

**Note:** This refresh behavior is **test-only**. Production ConfigSingleton is immutable.

---

## Pattern 2: @ConfigurationProperties (Class-Level Binding)

### Basic Usage

Bind an entire config section to a class:

```python
from sprigconfig import ConfigurationProperties

@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    url: str
    port: int
    username: str
    password: str

db = DatabaseConfig()
print(db.url)       # "postgresql://localhost/mydb"
print(db.port)      # 5432
print(db.username)  # "admin"
```

**Configuration file:**
```yaml
database:
  url: postgresql://localhost/mydb
  port: 5432
  username: admin
  password: ENC(gAAAAABh...)
```

### Type Hints Required

Only type-hinted attributes are bound:

```python
@ConfigurationProperties(prefix="app")
class AppConfig:
    name: str          # ✅ Bound from config
    version: str       # ✅ Bound from config
    custom_field       # ❌ Ignored (no type hint)
    _private: str      # ❌ Ignored (starts with underscore)
```

### Nested Object Binding

Nested classes auto-instantiate recursively:

```python
@ConfigurationProperties(prefix="connection")
class ConnectionPoolConfig:
    min_size: int
    max_size: int
    timeout: float

@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    url: str
    port: int
    pool: ConnectionPoolConfig  # Auto-instantiates nested config

db = DatabaseConfig()
print(db.url)              # "postgresql://localhost/mydb"
print(db.pool.min_size)    # 5
print(db.pool.max_size)    # 20
```

**Configuration file:**
```yaml
database:
  url: postgresql://localhost/mydb
  port: 5432
  pool:
    min_size: 5
    max_size: 20
    timeout: 30.0
```

**Note:** Nested classes must also be decorated with `@ConfigurationProperties`.

### Access to Config Object

The `._config` attribute provides access to the underlying `Config` object:

```python
@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    url: str
    port: int

db = DatabaseConfig()

# Bound attributes
print(db.url)                   # "postgresql://localhost/mydb"

# Config object methods
print(db._config.get("url"))    # Same value
print(db._config.to_dict())     # {"url": "...", "port": 5432}
db._config.dump("output.yml")   # Write to YAML

# Dotted-key access via Config
nested = db._config.get("some.nested.key")
```

### LazySecret Preservation

LazySecret values stay encrypted by default:

```python
@ConfigurationProperties(prefix="api")
class APIConfig:
    url: str
    secret_key: str  # Will be LazySecret if value is ENC(...)

api = APIConfig()
print(api.url)                    # "https://api.example.com"
print(type(api.secret_key))       # <class 'LazySecret'>

# Explicit decryption required
actual_key = api.secret_key.get()
```

### Refresh Behavior

Values are bound at instantiation time. Refresh requires creating a new instance:

```python
@ConfigurationProperties(prefix="app")
class AppConfig:
    name: str

# Initial load
ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
app = AppConfig()
print(app.name)  # "dev-app"

# Reload singleton (test-only)
reload_for_testing(profile="prod", config_dir=config_dir)
print(app.name)  # "dev-app" (unchanged - old instance)

# Create new instance to see updated config
app_new = AppConfig()
print(app_new.name)  # "prod-app"
```

### Custom __init__ Support

You can define custom `__init__` methods:

```python
@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    url: str
    port: int

    def __init__(self, override_port=None):
        # Custom initialization logic
        self.custom_field = "initialized"

        # Decorator will bind url and port after this
        if override_port:
            self.port = override_port

db = DatabaseConfig(override_port=3306)
print(db.url)          # From config
print(db.port)         # 3306 (overridden)
print(db.custom_field) # "initialized"
```

---

## Pattern 3: @config_inject (Function Parameter Injection)

### Basic Usage

Inject config values as function parameters:

```python
from sprigconfig import config_inject, ConfigValue

@config_inject
def connect_database(
    host: str = ConfigValue("database.host"),
    port: int = ConfigValue("database.port", default=5432),
    username: str = ConfigValue("database.username")
):
    print(f"Connecting to {host}:{port} as {username}")
    # ... connection logic ...

# Call without arguments - values injected from config
connect_database()
```

**Configuration file:**
```yaml
database:
  host: localhost
  port: 5432
  username: admin
```

### Override Support

Explicit arguments override config values:

```python
@config_inject
def connect_database(
    host: str = ConfigValue("database.host"),
    port: int = ConfigValue("database.port", default=5432),
    username: str = ConfigValue("database.username")
):
    return f"Connecting to {host}:{port} as {username}"

# Use all config values
result = connect_database()
# → "Connecting to localhost:5432 as admin"

# Override specific values
result = connect_database(host="prod-db.example.com")
# → "Connecting to prod-db.example.com:5432 as admin"

# Override all values
result = connect_database(host="remote", port=3306, username="root")
# → "Connecting to remote:3306 as root"
```

### Required Parameters

Parameters without defaults must be provided at call time:

```python
@config_inject
def process_data(
    input_path: str,  # Required (no default)
    batch_size: int = ConfigValue("processing.batch_size", default=100)
):
    print(f"Processing {input_path} with batch size {batch_size}")

# Must provide input_path
process_data(input_path="data.csv")  # ✅ Works

# Error: missing required parameter
process_data()  # ❌ TypeError: missing 1 required positional argument: 'input_path'
```

### LazySecret Handling

ConfigValue in function parameters supports both decrypt modes:

```python
@config_inject
def send_email(
    smtp_host: str = ConfigValue("email.smtp.host"),
    smtp_password: str = ConfigValue("email.smtp.password", decrypt=True)
):
    # smtp_password is auto-decrypted
    server = smtplib.SMTP(smtp_host)
    server.login("user", smtp_password)
```

### Refresh Behavior

ConfigValue resolves on each function call:

```python
@config_inject
def get_api_url(
    url: str = ConfigValue("api.url")
):
    return url

# Initial load
ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
print(get_api_url())  # "https://dev-api.example.com"

# Reload singleton (test-only)
reload_for_testing(profile="prod", config_dir=config_dir)
print(get_api_url())  # "https://prod-api.example.com" - auto-refreshed!
```

---

## Comparison: When to Use Which Pattern

| Pattern | Best For | Pros | Cons |
|---------|----------|------|------|
| **ConfigValue** | Scattered config values across a class | Fine-grained control, auto-refresh | Slight overhead per access |
| **@ConfigurationProperties** | Grouped config sections | Batch binding, zero per-access overhead | Refresh requires new instance |
| **@config_inject** | Function-level dependency injection | Testing-friendly, override support | Per-call overhead |
| **Config.get()** | Dynamic/conditional config access | Maximum flexibility | Verbose, no type safety |

### Use ConfigValue When:

- You have a class that needs a few config values
- Values are scattered across different config sections
- You want auto-refresh behavior in tests
- You want type conversion and clear error messages

```python
class EmailService:
    smtp_host: str = ConfigValue("email.smtp.host")
    smtp_port: int = ConfigValue("email.smtp.port")
    from_addr: str = ConfigValue("email.from")
```

### Use @ConfigurationProperties When:

- You have a cohesive config section (e.g., "database", "api", "logging")
- You want to group related configuration together
- You need nested object binding
- You want zero per-access overhead

```python
@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    url: str
    port: int
    username: str
    pool: ConnectionPoolConfig
```

### Use @config_inject When:

- You want to inject config into functions
- You need to support explicit overrides
- You're writing testable utility functions

```python
@config_inject
def send_notification(
    api_key: str = ConfigValue("notifications.api_key", decrypt=True),
    timeout: int = ConfigValue("notifications.timeout", default=30)
):
    # ...
```

### Use Config.get() When:

- You need dynamic key resolution
- You're accessing config conditionally
- You need maximum flexibility
- You're debugging/introspecting config

```python
cfg = ConfigSingleton.get()
for service in ["api", "db", "cache"]:
    url = cfg.get(f"{service}.url")  # Dynamic key
```

---

## Complete Example

Here's a real-world example combining all patterns:

**Configuration (application.yml):**
```yaml
app:
  name: MyApp
  version: 1.0.0
  debug: false

database:
  url: postgresql://localhost/mydb
  port: 5432
  username: admin
  password: ENC(gAAAAABh...)
  pool:
    min_size: 5
    max_size: 20

email:
  smtp:
    host: smtp.gmail.com
    port: 587
  from: noreply@example.com
  api_key: ENC(gAAAAABi...)

api:
  base_url: https://api.example.com
  timeout: 30
  retries: 3
```

**Application Code:**

```python
from sprigconfig import (
    ConfigSingleton,
    ConfigValue,
    ConfigurationProperties,
    config_inject,
)

# Initialize at startup
ConfigSingleton.initialize(profile="prod", config_dir="./config")

# Pattern 2: Class-level binding for grouped config
@ConfigurationProperties(prefix="pool")
class ConnectionPoolConfig:
    min_size: int
    max_size: int

@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    url: str
    port: int
    username: str
    password: str  # LazySecret
    pool: ConnectionPoolConfig

# Pattern 1: Field-level binding for scattered values
class EmailService:
    smtp_host: str = ConfigValue("email.smtp.host")
    smtp_port: int = ConfigValue("email.smtp.port")
    from_address: str = ConfigValue("email.from")
    api_key: str = ConfigValue("email.api_key", decrypt=True)

    def send(self, to: str, subject: str, body: str):
        # api_key already decrypted
        server = smtplib.SMTP(self.smtp_host, self.smtp_port)
        # ...

# Pattern 3: Function injection for utilities
@config_inject
def make_api_request(
    endpoint: str,
    base_url: str = ConfigValue("api.base_url"),
    timeout: int = ConfigValue("api.timeout", default=30),
    retries: int = ConfigValue("api.retries", default=3)
):
    url = f"{base_url}/{endpoint}"
    # ... request logic with retries ...

# Usage
db = DatabaseConfig()
print(db.url)              # From config
print(db.pool.min_size)    # Nested binding

email = EmailService()
email.send("user@example.com", "Hello", "World")

response = make_api_request("users/123")  # Uses config
response = make_api_request("users/123", timeout=60)  # Override
```

---

## Security Best Practices

### LazySecret Encryption

1. **Default to decrypt=False**
   ```python
   # Good: Secret stays encrypted
   admin_key: str = ConfigValue("app.admin_key", decrypt=False)
   if is_admin:
       key = admin_key.get()  # Decrypt only when needed
   ```

2. **Use decrypt=True sparingly**
   ```python
   # Acceptable: Frequently-used secret in hot path
   db_password: str = ConfigValue("database.password", decrypt=True)
   connection = connect(host, user, db_password)
   ```

3. **Never log decrypted secrets**
   ```python
   # BAD
   logger.info(f"Using password: {db_password}")

   # GOOD
   logger.info("Database connection configured")
   ```

### Key Management

1. **Use environment variables**
   ```bash
   export APP_SECRET_KEY="your-fernet-key-here"
   ```

2. **Different keys per environment**
   ```bash
   # Dev
   export APP_SECRET_KEY="dev-key..."

   # Prod
   export APP_SECRET_KEY="prod-key..."
   ```

3. **Rotate keys regularly**
   - Quarterly rotation recommended
   - Re-encrypt all secrets after key rotation

### Audit Access

```python
import logging

class SecureAPIClient:
    api_key: str = ConfigValue("api.secret_key", decrypt=False)

    def make_request(self):
        # Log access (not value)
        logging.info("Decrypting API key for request")
        key = self.api_key.get()

        try:
            # Use key
            response = requests.get(url, headers={"Authorization": f"Bearer {key}"})
        finally:
            # Optionally zero out key in memory (best effort)
            key = None
```

---

## Testing with Refresh

### Test Fixtures

Use the provided test utilities for config reloading:

```python
# tests/test_my_service.py
import pytest
from sprigconfig import ConfigSingleton
from tests.utils.config_test_utils import reload_for_testing

@pytest.fixture(autouse=True)
def clear_singleton():
    """Ensure clean singleton state for each test."""
    ConfigSingleton._clear_all()
    yield
    ConfigSingleton._clear_all()

def test_config_value_refresh(config_dir):
    """ConfigValue auto-refreshes after reload."""

    class Service:
        timeout: int = ConfigValue("service.timeout")

    # Initial load
    ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
    service = Service()
    assert service.timeout == 30

    # Reload
    reload_for_testing(profile="prod", config_dir=config_dir)
    assert service.timeout == 60  # Auto-refreshed!

def test_configuration_properties_refresh(config_dir):
    """@ConfigurationProperties requires new instance after reload."""

    @ConfigurationProperties(prefix="app")
    class AppConfig:
        name: str

    # Initial load
    ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
    app = AppConfig()
    assert app.name == "dev-app"

    # Reload
    reload_for_testing(profile="prod", config_dir=config_dir)
    assert app.name == "dev-app"  # Old instance unchanged

    # New instance sees new config
    app_new = AppConfig()
    assert app_new.name == "prod-app"
```

### Mocking for Tests

Use @config_inject for easier testing:

```python
# Production code
@config_inject
def process_data(
    input_path: str,
    batch_size: int = ConfigValue("processing.batch_size", default=100)
):
    # ... processing logic ...

# Test code - no config needed
def test_process_data():
    # Override config value with test value
    result = process_data(input_path="test.csv", batch_size=10)
    assert result is not None
```

---

## Migration Guide

### Gradual Adoption

You can adopt dependency injection gradually without rewriting existing code:

**Step 1:** Keep existing Config.get() calls
```python
# Existing code - keep as-is
cfg = ConfigSingleton.get()
db_url = cfg.get("database.url")
```

**Step 2:** Use dependency injection for new code
```python
# New service - use dependency injection
class NewService:
    db_url: str = ConfigValue("database.url")
```

**Step 3:** Optionally migrate old code over time
```python
# Refactor when touching old code
class OldService:
    # Before:
    # def __init__(self):
    #     cfg = ConfigSingleton.get()
    #     self.db_url = cfg.get("database.url")

    # After:
    db_url: str = ConfigValue("database.url")
```

### No Forced Migration

Config.get() will be supported **indefinitely**. Choose the pattern that fits your code best:

- **Config.get()**: Dynamic lookups, debugging
- **ConfigValue**: Field-level binding
- **@ConfigurationProperties**: Class-level binding
- **@config_inject**: Function injection

---

## Troubleshooting

### Error: ConfigSingleton not initialized

```
ConfigLoadError: ConfigSingleton not initialized when accessing MyService.db_url
Hint: Call ConfigSingleton.initialize(profile, config_dir) at startup
```

**Solution:** Ensure you call `ConfigSingleton.initialize()` before accessing any dependency injection-bound values:

```python
# At application startup
ConfigSingleton.initialize(profile="prod", config_dir="./config")

# Then use services
service = MyService()
```

### Error: Config key not found

```
ConfigLoadError: Config key 'database.url' not found and no default provided.
Available keys at 'database': ['host', 'port', 'name']
Hint: Check your config files or add default= parameter
```

**Solution:** Either add the key to your config file or provide a default:

```python
# Option 1: Add to config
# database:
#   url: postgresql://localhost/mydb

# Option 2: Provide default
db_url: str = ConfigValue("database.url", default="postgresql://localhost/mydb")
```

### Error: Cannot convert type

```
ConfigLoadError: Cannot convert config value to type 'int'
Key: database.port
Value: "not_a_number" (type: str)
Expected: int
```

**Solution:** Fix the value in your config file:

```yaml
database:
  port: 5432  # Not "not_a_number"
```

### Error: Failed to decrypt LazySecret

```
ConfigLoadError: Failed to decrypt LazySecret for key 'api.secret_key'
Hint: Check APP_SECRET_KEY environment variable
```

**Solution:** Ensure `APP_SECRET_KEY` is set:

```bash
export APP_SECRET_KEY="your-fernet-key-here"
```

---

## Performance Considerations

### ConfigValue Overhead

- **Per-access**: ~1-2μs
- **Impact**: Negligible for normal use
- **Optimization**: Cache in local variables for hot loops

```python
class Processor:
    batch_size: int = ConfigValue("processor.batch_size")

    def process_millions(self, items):
        batch_size = self.batch_size  # Cache once
        for item in items:
            process(item, batch_size)  # Use cached value
```

### @ConfigurationProperties Overhead

- **Instantiation**: ~10-50μs (one-time)
- **Per-access**: 0μs (direct attribute access)
- **Best for**: Grouped config accessed frequently

### @config_inject Overhead

- **Per-call**: ~5-10μs
- **Impact**: Negligible for normal functions
- **Optimization**: Not needed for most use cases

---

## API Reference

### ConfigValue

```python
ConfigValue(key: str, *, default: Any = None, decrypt: bool = False)
```

**Parameters:**
- `key` (str): Dotted config key (e.g., "database.url")
- `default` (Any, optional): Default value if key missing
- `decrypt` (bool, optional): Auto-decrypt LazySecret (default: False)

**Returns:** Resolved config value with type conversion

**Example:**
```python
timeout: int = ConfigValue("service.timeout", default=30)
api_key: str = ConfigValue("api.key", decrypt=True)
```

### @ConfigurationProperties

```python
@ConfigurationProperties(prefix: str)
```

**Parameters:**
- `prefix` (str): Dotted config prefix (e.g., "database")

**Decorator for:** Classes with type-hinted attributes

**Example:**
```python
@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    url: str
    port: int
```

### @config_inject

```python
@config_inject
```

**Decorator for:** Functions with ConfigValue parameters

**Example:**
```python
@config_inject
def connect(host: str = ConfigValue("db.host")):
    pass
```

---

## Next Steps

- **Try it out**: Update your code to use dependency injection
- **Run tests**: Ensure no regressions with existing tests
- **Provide feedback**: Report issues or suggestions
- **Read design docs**: See `src/sprigconfig/injection.md` for implementation details

For questions or issues, please refer to the SprigConfig documentation or open an issue on the project repository.
