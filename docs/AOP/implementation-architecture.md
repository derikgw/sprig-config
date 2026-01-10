# AOP Implementation Architecture

## Overview

This document details the technical architecture for Spring Boot-style AOP configuration injection in SprigConfig. It covers the three core patterns, their implementation strategies, and integration with the existing SprigConfig architecture.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Application Code                     │
│                                                               │
│  ┌────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  ConfigValue   │  │ @Configuration   │  │ @config_     │ │
│  │  Descriptor    │  │ Properties       │  │ inject       │ │
│  └────────┬───────┘  └────────┬─────────┘  └──────┬───────┘ │
│           │                   │                    │         │
└───────────┼───────────────────┼────────────────────┼─────────┘
            │                   │                    │
            │    ┌──────────────▼────────────────┐   │
            │    │  sprigconfig/injection.py     │   │
            │    │  - ConfigValue class          │   │
            │    │  - ConfigurationProperties()  │   │
            │    │  - config_inject()            │   │
            │    │  - Type conversion logic      │   │
            │    └──────────────┬────────────────┘   │
            │                   │                    │
            └───────────────────┼────────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │  ConfigSingleton.get() │
                    │  (Thread-safe access)  │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │    Config Instance     │
                    │  - Dotted-key access   │
                    │  - LazySecret support  │
                    │  - Deep merge results  │
                    └────────────────────────┘
```

## Core Components

### 1. ConfigValue Descriptor

**Responsibility:** Lazy resolution of individual config values with type conversion and LazySecret handling.

**Design Pattern:** Python descriptor protocol

**Key Methods:**
- `__init__(key, *, default, decrypt)` - Initialize with config key and options
- `__set_name__(owner, name)` - Capture type hint from owner class
- `__get__(obj, objtype)` - Resolve value from ConfigSingleton on access

**Data Flow:**
```
User Access: service.db_url
     ↓
__get__() called by Python
     ↓
ConfigSingleton.get() → Config instance
     ↓
Config.get(self.key, self.default)
     ↓
isinstance(value, LazySecret)?
     ├─ Yes, decrypt=True → value.get()
     ├─ Yes, decrypt=False → return LazySecret
     └─ No → continue
     ↓
Type conversion (if type hint present)
     ↓
Return converted value
```

**Performance Characteristics:**
- No caching (always resolves from singleton)
- Overhead: ~1-2μs per access
- Thread-safe (ConfigSingleton.get() is thread-safe)

**Security:**
- `decrypt=False` (default) - Returns LazySecret object (encrypted in memory)
- `decrypt=True` - Auto-decrypts (plaintext in memory)
- No descriptor-level caching of decrypted values

---

### 2. @ConfigurationProperties Decorator

**Responsibility:** Auto-bind entire config sections to class instances with nested object support.

**Design Pattern:** Decorator wrapping `__init__`

**Key Operations:**
1. Preserve original `__init__`
2. Wrap with binding logic
3. Resolve config section from prefix
4. Store Config object in `._config` attribute
5. Auto-bind type-hinted attributes
6. Handle nested object instantiation

**Data Flow:**
```
User: db = DatabaseConfig()
     ↓
Decorated __init__() called
     ↓
Call original __init__() (if present)
     ↓
ConfigSingleton.get() → Config instance
     ↓
Config.get(prefix) → section
     ↓
Store as ._config attribute
     ↓
For each type-hinted attribute:
  ├─ Get value from section
  ├─ Is type hint a class? → Auto-instantiate (nested)
  ├─ Is value LazySecret? → Keep as-is
  └─ Convert type → setattr()
     ↓
Instance fully bound
```

**Nested Object Binding:**
```python
@ConfigurationProperties(prefix="app.database")
class DatabaseConfig:
    connection: ConnectionPoolConfig  # Auto-instantiates

@ConfigurationProperties(prefix="connection")
class ConnectionPoolConfig:
    min_size: int
    max_size: int

# YAML structure:
app:
  database:
    connection:
      min_size: 5
      max_size: 20

# Binding flow:
# 1. DatabaseConfig.__init__() called
# 2. Resolves app.database section
# 3. Finds connection: {...}
# 4. Detects type hint is ConnectionPoolConfig class
# 5. Instantiates ConnectionPoolConfig()
# 6. ConnectionPoolConfig resolves its prefix (connection)
# 7. Binds min_size and max_size
# 8. Assigns to db.connection
```

**Performance Characteristics:**
- One-time cost at instantiation (~10-50μs)
- No per-access overhead (values stored in instance)
- Refresh requires new instance creation

**Flexibility:**
- `._config` provides escape hatch to Config methods
- Access both bound attributes AND Config object features

---

### 3. @config_inject Decorator

**Responsibility:** Inject config values into function parameters with override support.

**Design Pattern:** Function wrapper using inspect.signature()

**Key Operations:**
1. Capture function signature
2. Bind positional arguments
3. Bind keyword arguments
4. Resolve ConfigValue defaults for missing parameters
5. Call function with complete arguments

**Data Flow:**
```
User: connect_db(user="admin")
     ↓
Wrapper function called
     ↓
inspect.signature(func) → parameter info
     ↓
Build bound_args dict:
  ├─ Positional args → bound_args
  ├─ Keyword args → bound_args (override)
  └─ For missing params with ConfigValue default:
      └─ ConfigValue.__get__() → bound_args
     ↓
func(**bound_args)
```

**Override Semantics:**
```python
@config_inject
def connect(
    host: str = ConfigValue("db.host"),
    port: int = ConfigValue("db.port", default=5432),
    user: str = None
):
    pass

# Call scenarios:
connect(user="admin")                    # Uses config for host/port
connect(user="admin", host="localhost")  # Overrides host
connect("admin", "localhost", 5432)      # All positional (overrides all)
```

**Performance Characteristics:**
- Per-call overhead: ~5-10μs
- Signature introspection cached by Python
- ConfigValue resolution: ~1-2μs per parameter

---

## Type Conversion System

### Conversion Matrix

| Type Hint | YAML Type | Conversion | Example |
|-----------|-----------|------------|---------|
| `str` | any | `str(value)` | 5432 → "5432" |
| `int` | str | `int(value)` | "5432" → 5432 |
| `int` | int | pass through | 5432 → 5432 |
| `float` | str | `float(value)` | "3.14" → 3.14 |
| `bool` | str | `value.lower() in ('true', ...)` | "true" → True |
| `bool` | bool | pass through | true → True |
| `list` | list | pass through | [1, 2, 3] → [1, 2, 3] |
| `dict` | dict | pass through | {...} → {...} |
| Custom | dict | Auto-instantiate (if @ConfigurationProperties) | {...} → NestedConfig(...) |

### Special Cases

**LazySecret:**
- Never converted
- Passed through unchanged
- `decrypt` parameter controls handling at descriptor level

**Config:**
- Never converted
- Returned as Config instance
- Allows chaining: `cfg.get("database").get("host")`

**None/Missing:**
- Returns default if provided
- Raises ConfigLoadError if no default

### Error Messages

**Type Conversion Failure:**
```
ConfigLoadError: Cannot convert config value to type 'int'
Key: database.port
Value: "not_a_number" (type: str)
Expected: int
Descriptor: ConfigValue('database.port') on MyService.db_port
Reason: invalid literal for int() with base 10: 'not_a_number'
Hint: Check your config file and ensure the value is a valid integer
```

**Missing Key:**
```
ConfigLoadError: Config key 'database.url' not found and no default provided.
Descriptor: ConfigValue('database.url') on MyService.db_url
Hint: Check your config files or add default= parameter
Available keys at 'database': ['host', 'port', 'name']
```

---

## LazySecret Integration

### Security Architecture

**Zero-Trust by Default:**
```
ConfigValue("api.key", decrypt=False)  # Default
     ↓
Returns LazySecret object
     ↓
Secret stays encrypted in memory
     ↓
User must call .get() to decrypt
     ↓
Minimizes exposure window
```

**Explicit Decryption:**
```
ConfigValue("api.key", decrypt=True)
     ↓
Auto-decrypts at binding time
     ↓
Plaintext stored in attribute/variable
     ↓
More convenient but less secure
     ↓
Still better than plaintext YAML
```

### Memory Layout

**decrypt=False (default):**
```
Memory:
┌─────────────────┐
│ ConfigValue     │  (Descriptor, no data)
├─────────────────┤
│ LazySecret      │
│  _encrypted_value: "gAAA..."  (Fernet ciphertext)
│  _decrypted_value: None       (Not yet decrypted)
│  _key: "APP_SECRET_KEY"
└─────────────────┘
```

**After .get() called:**
```
Memory:
┌─────────────────┐
│ LazySecret      │
│  _encrypted_value: "gAAA..."
│  _decrypted_value: "actual_secret"  (Cached, plaintext)
│  _key: "APP_SECRET_KEY"
└─────────────────┘
```

**decrypt=True:**
```
Memory:
┌─────────────────┐
│ ConfigValue     │  (Descriptor, no data)
├─────────────────┤
│ str             │
│  "actual_secret"  (Plaintext, immediately)
└─────────────────┘
```

### Security Trade-offs

| Approach | Security | Convenience | Use Case |
|----------|----------|-------------|----------|
| `decrypt=False` | Highest | Low | Rarely-accessed secrets (emergency keys, admin passwords) |
| `decrypt=True` | Medium | High | Frequently-used secrets (DB passwords, API keys) |
| Plaintext YAML | Lowest | Highest | Non-secrets only |

---

## Test-Only Refresh Mechanism

### Architecture Constraint

**Production:** ConfigSingleton is immutable (no reload)
**Testing:** Fixtures wrap reload_for_testing()

### Refresh Behavior by Pattern

**ConfigValue Descriptor:**
```python
class Service:
    timeout: int = ConfigValue("service.timeout")

# Initial load
ConfigSingleton.initialize(profile="dev", ...)
service = Service()
print(service.timeout)  # 30 (from dev config)

# Test reload
reload_for_testing(profile="prod", ...)  # Clears + re-initializes singleton
print(service.timeout)  # 60 (from prod config)
# ↑ Descriptor __get__() calls ConfigSingleton.get() → new singleton!
```

**Why it works:** ConfigValue has no caching, always resolves from current singleton.

**@ConfigurationProperties:**
```python
@ConfigurationProperties(prefix="app")
class AppConfig:
    name: str

# Initial load
ConfigSingleton.initialize(profile="dev", ...)
app = AppConfig()
print(app.name)  # "dev-app" (bound at instantiation)

# Test reload
reload_for_testing(profile="prod", ...)
print(app.name)  # "dev-app" (unchanged - old instance)

# Create new instance
app_new = AppConfig()
print(app_new.name)  # "prod-app" (reads from new singleton)
```

**Why it differs:** Values bound at instantiation (stored in `__dict__`), not descriptors.

**@config_inject:**
```python
@config_inject
def connect(host: str = ConfigValue("db.host")):
    return host

# Initial load
ConfigSingleton.initialize(profile="dev", ...)
print(connect())  # "dev-host"

# Test reload
reload_for_testing(profile="prod", ...)
print(connect())  # "prod-host"
# ↑ ConfigValue.__get__() called on each function call
```

**Why it works:** ConfigValue resolved on each function call.

### Test Fixtures

**aop_fixtures.py:**
```python
@pytest.fixture
def reload_config():
    """Wrapper around reload_for_testing for AOP tests."""
    def _reload(profile: str, config_dir: Path):
        return reload_for_testing(profile=profile, config_dir=config_dir)
    return _reload

@pytest.fixture(autouse=True)
def clear_singleton_for_aop():
    """Ensure clean singleton state for each test."""
    ConfigSingleton._clear_all()
    yield
    ConfigSingleton._clear_all()
```

### Refresh Testing Pattern

```python
def test_config_value_refresh(config_dir, reload_config):
    """ConfigValue descriptors auto-refresh on reload."""

    class Service:
        timeout: int = ConfigValue("service.timeout")

    # Initial load
    ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
    service = Service()
    assert service.timeout == 30

    # Reload
    reload_config(profile="prod", config_dir=config_dir)

    # Same instance, new value (descriptor re-resolves)
    assert service.timeout == 60

def test_configuration_properties_refresh(config_dir, reload_config):
    """@ConfigurationProperties requires new instance after reload."""

    @ConfigurationProperties(prefix="app")
    class AppConfig:
        name: str

    # Initial load
    ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
    app = AppConfig()
    assert app.name == "dev-app"

    # Reload
    reload_config(profile="prod", config_dir=config_dir)

    # Old instance unchanged
    assert app.name == "dev-app"

    # New instance sees new config
    app_new = AppConfig()
    assert app_new.name == "prod-app"
```

---

## Thread Safety

### ConfigSingleton Lock

**Initialization:**
```python
_lock = threading.Lock()

@classmethod
def initialize(cls, *, profile, config_dir):
    with cls._lock:
        if cls._instance is not None:
            raise ConfigLoadError("Already initialized")
        # ... load and store ...
```

**Access (Lock-Free):**
```python
@classmethod
def get(cls):
    if cls._instance is None:
        raise ConfigLoadError("Not initialized")
    return cls._instance  # No lock needed (immutable)
```

### AOP Thread Safety

**ConfigValue:**
- `__get__()` calls `ConfigSingleton.get()` (thread-safe)
- No descriptor-level state (thread-safe)
- Multiple threads can access concurrently

**@ConfigurationProperties:**
- Instantiation calls `ConfigSingleton.get()` (thread-safe)
- Instance `__dict__` not shared across threads
- Safe to instantiate in multiple threads

**@config_inject:**
- Signature introspection cached by Python (thread-safe)
- ConfigValue resolution per-call (thread-safe)
- No shared state

### Test Reload Thread Safety

**Caution:** reload_for_testing() is NOT thread-safe
- Uses `ConfigSingleton._clear_all()` (no lock)
- Only safe in single-threaded tests
- Must use `pytest -n 0` (no xdist) for reload tests

---

## Performance Optimization Strategies

### When to Cache

**Hot Loops:**
```python
class Processor:
    batch_size: int = ConfigValue("processor.batch_size")

    def process_millions(self, items):
        batch_size = self.batch_size  # Cache once
        for item in items:
            process(item, batch_size)  # Use cached value
```

**Avoid:**
```python
# BAD: Descriptor access in tight loop
for item in items:
    process(item, self.batch_size)  # 1-2μs overhead per iteration
```

### When to Use @ConfigurationProperties

**Better for grouped config:**
```python
# Better: One-time binding cost
@ConfigurationProperties(prefix="processor")
class ProcessorConfig:
    batch_size: int
    timeout: int
    retries: int

config = ProcessorConfig()  # ~10-50μs once
for item in items:
    process(item, config.batch_size)  # No descriptor overhead
```

**Worse for scattered values:**
```python
# Worse: Binds entire section, but only uses one field
@ConfigurationProperties(prefix="app")
class AppConfig:
    # ... 50 fields ...
    processor_batch_size: int

# Only need one value, but binding all 50
```

---

## Integration with Existing SprigConfig

### No Changes to Core Modules

**Unchanged:**
- `config.py` - Config class
- `config_singleton.py` - Singleton pattern
- `config_loader.py` - Loading and merging
- `lazy_secret.py` - Secret handling
- `deepmerge.py` - Deep merge logic

**Additive Only:**
- `injection.py` - NEW module
- `__init__.py` - Add exports

### Backward Compatibility

**Existing code continues to work:**
```python
# OLD WAY (still supported)
cfg = ConfigSingleton.get()
db_url = cfg.get("database.url")

# NEW WAY (opt-in)
class Service:
    db_url: str = ConfigValue("database.url")
```

**No forced migration:**
- Config.get() will never be deprecated
- AOP is optional enhancement
- Choose based on code clarity

---

## Error Handling Philosophy

### Design Principles

1. **Clear Context:** Include key, value, type, descriptor location
2. **Actionable Hints:** Suggest fixes
3. **Full Stack Trace:** Preserve original error
4. **Consistent Format:** All errors follow same template

### Error Template

```
ConfigLoadError: <brief description>
<Key context>
<Value context>
<Type context>
<Location context>
Reason: <underlying error>
Hint: <suggested fix>
```

### Examples by Scenario

**Missing Key:**
```
ConfigLoadError: Config key 'database.url' not found and no default provided.
Descriptor: ConfigValue('database.url') on MyService.db_url
Hint: Check your config files or add default= parameter
Available keys at 'database': ['host', 'port', 'name']
```

**Type Conversion:**
```
ConfigLoadError: Cannot convert config value to type 'int'
Key: database.port
Value: "not_a_number" (type: str)
Expected: int
Descriptor: ConfigValue('database.port') on MyService.db_port
Reason: invalid literal for int() with base 10: 'not_a_number'
Hint: Check your config file and ensure the value is a valid integer
```

**LazySecret Decryption:**
```
ConfigLoadError: Failed to decrypt LazySecret for key 'api.secret_key'
Descriptor: ConfigValue('api.secret_key', decrypt=True) on ApiClient.api_key
Reason: Invalid Fernet key or ciphertext
Hint: Check APP_SECRET_KEY environment variable
```

**Singleton Not Initialized:**
```
ConfigLoadError: ConfigSingleton not initialized when accessing MyService.db_url
Descriptor: ConfigValue('database.url') on MyService.db_url
Required: Call ConfigSingleton.initialize(profile, config_dir) at startup
Hint: Add ConfigSingleton.initialize() to your application startup code
```

**Nested Class Instantiation:**
```
ConfigLoadError: Failed to instantiate nested config class PoolConfig
Parent: DatabaseConfig.pool
Reason: __init__() missing 1 required positional argument: 'min_size'
Hint: Ensure nested class has @ConfigurationProperties decorator and all required fields in config
```

---

## Design Rationale

### Why Descriptors for ConfigValue?

**Alternatives Considered:**

1. **Property Factory:**
   ```python
   def config_property(key):
       return property(lambda self: ConfigSingleton.get().get(key))
   ```
   - **Rejected:** No type hints, no __set_name__ capture

2. **Cached Attributes:**
   ```python
   class MyService:
       def __init__(self):
           self.db_url = ConfigSingleton.get().get("database.url")
   ```
   - **Rejected:** No auto-refresh for tests, verbose

3. **Descriptor (Chosen):**
   - Type hint capture via __set_name__
   - Lazy resolution (supports test refresh)
   - Pythonic attribute access
   - Clear error messages with context

### Why Decorator for @ConfigurationProperties?

**Alternatives Considered:**

1. **Base Class:**
   ```python
   class DatabaseConfig(ConfigBase):
       url: str
   ```
   - **Rejected:** Forces inheritance, less flexible

2. **Metaclass:**
   ```python
   class DatabaseConfig(metaclass=ConfigMeta):
       url: str
   ```
   - **Rejected:** Too magical, harder to debug

3. **Decorator (Chosen):**
   - Non-invasive (no base class)
   - Clear intent (visible in code)
   - Flexible (can wrap __init__)
   - Familiar pattern (similar to @dataclass)

### Why inspect.signature for @config_inject?

**Alternatives Considered:**

1. **Manual Argument Parsing:**
   ```python
   def wrapper(*args, **kwargs):
       # Manually bind positional args...
   ```
   - **Rejected:** Error-prone, doesn't handle all cases

2. **inspect.signature (Chosen):**
   - Handles all parameter types
   - Respects default values
   - Clear override semantics
   - Pythonic introspection

---

## Future Enhancements (Out of Scope)

**Validation Framework:**
- `@Min(1)`, `@Max(65535)` for bounds checking
- `@Pattern("regex")` for string validation
- `@NotNull`, `@Email`, etc. (JSR-303 style)

**Complex Type Hints:**
- `list[str]` - Type-check list elements
- `dict[str, int]` - Type-check dict values
- `Optional[str]` - Explicit None handling
- `Union[int, str]` - Multiple valid types

**Dynamic Reload (Production):**
- File watcher for config changes
- Hot reload with graceful transition
- Notification system for bound values

**Nested Binding Enhancements:**
- `list[NestedConfig]` - Bind list of config objects
- `dict[str, NestedConfig]` - Bind dict of config objects
- Circular reference detection

**Performance Optimizations:**
- Optional caching mode for ConfigValue
- Batch binding for @ConfigurationProperties
- Lazy attribute population

---

## Conclusion

This architecture provides a solid foundation for Spring Boot-style AOP configuration injection in SprigConfig while maintaining:

- **Security:** Zero-trust LazySecret handling
- **Simplicity:** Type conversion only (no complex validation)
- **Flexibility:** Three patterns for different use cases
- **Compatibility:** Existing Config.get() unchanged
- **Testability:** Test-only refresh via fixtures
- **Performance:** Minimal overhead (<5μs)

The design prioritizes clarity, security, and backward compatibility over clever abstractions.
