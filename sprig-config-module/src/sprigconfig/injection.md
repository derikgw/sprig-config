# sprigconfig/injection.md

## Overview

The `injection.py` module provides Spring Boot-style dependency injection for SprigConfig. It implements three patterns for declarative configuration binding:

1. **ConfigValue** - Descriptor for lazy field-level binding
2. **@ConfigurationProperties** - Decorator for class-level auto-binding
3. **@config_inject** - Decorator for function parameter injection

All patterns integrate with the existing `ConfigSingleton` and support type conversion, LazySecret handling, and clear error messages.

## Design Philosophy

### Zero-Trust Security

LazySecret values remain encrypted in memory by default. Users must explicitly opt-in to auto-decryption via the `decrypt=True` parameter.

**decrypt=False (default)**:
- Returns LazySecret object
- Secret stays encrypted in memory
- Must call `.get()` to decrypt
- Minimizes exposure window

**decrypt=True**:
- Auto-decrypts at binding time
- Plaintext stored in memory
- More convenient for frequently-used secrets
- Still better than plaintext YAML

### Lazy Resolution (ConfigValue)

ConfigValue descriptors resolve from ConfigSingleton on every access with no caching. This design choice:
- Enables test refresh behavior (descriptors see new singleton after reload)
- Adds minimal overhead (~1-2μs per access)
- Maintains simplicity (no cache invalidation logic)
- Follows Python descriptor protocol naturally

### Eager Binding (@ConfigurationProperties)

The @ConfigurationProperties decorator binds values at instance creation time and stores them in the instance `__dict__`. This design choice:
- One-time binding cost (~10-50μs per instance)
- Zero per-access overhead (direct attribute access)
- Refresh requires creating new instance
- Preserves original Config object via `._config` attribute

### Test-Only Refresh

Production code maintains ConfigSingleton immutability. Test fixtures wrap `reload_for_testing()` to enable test isolation. No production code for reload.

**ConfigValue**: Auto-refreshes on access (reads new singleton)
**@ConfigurationProperties**: Requires new instance after reload
**@config_inject**: Auto-refreshes on each function call

---

## ConfigValue Descriptor

### Python Descriptor Protocol

ConfigValue implements the descriptor protocol via `__get__`, `__set__`, and `__set_name__`:

```python
class ConfigValue:
    def __init__(self, key, *, default=None, decrypt=False):
        self.key = key
        self.default = default
        self.decrypt = decrypt

    def __set_name__(self, owner, name):
        # Called when descriptor assigned to class attribute
        # Captures type hint and owner context for error messages
        self._owner_name = owner.__name__
        self._attr_name = name
        self._type_hint = owner.__annotations__.get(name)

    def __get__(self, obj, objtype=None):
        # Called when attribute accessed on instance
        if obj is None:
            return self  # Class access

        # Lazy resolution (always reads from current singleton)
        cfg = ConfigSingleton.get()
        value = cfg.get(self.key, self.default)

        # Handle LazySecret
        if isinstance(value, LazySecret):
            if self.decrypt:
                value = value.get()  # Auto-decrypt

        # Type conversion
        if self._type_hint and value is not None:
            value = self._convert_type(value, self._type_hint)

        return value

    def __set__(self, obj, value):
        # Prevent overwriting (read-only)
        raise AttributeError("ConfigValue descriptors are read-only")
```

### Resolution Flow

```
User Access: service.db_url
     ↓
Python calls ConfigValue.__get__(service, Service)
     ↓
ConfigSingleton.get() → Config instance
     ↓
Config.get("database.url", default=None)
     ↓
isinstance(value, LazySecret)?
  ├─ Yes + decrypt=True → value.get()
  ├─ Yes + decrypt=False → return LazySecret
  └─ No → continue
     ↓
Type conversion (if type hint present)
     ↓
Return converted value
```

### Type Hint Capture

`__set_name__` is called by Python when the descriptor is assigned to a class attribute:

```python
class MyService:
    timeout: int = ConfigValue("service.timeout")
    #      ^^^  This type hint is captured by __set_name__

# Python calls: ConfigValue.__set_name__(MyService, "timeout")
# Descriptor captures: _type_hint = int
```

The captured type hint drives automatic type conversion:
- YAML `"30"` (str) → Python `30` (int)
- YAML `true` (bool) → Python `True` (bool)
- YAML `["a", "b"]` (list) → Python `["a", "b"]` (list)

### Error Context

ConfigValue provides rich error messages by capturing owner/attribute context:

```
ConfigLoadError: Config key 'database.url' not found and no default provided.
Descriptor: ConfigValue('database.url') on MyService.db_url
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
           Owner class and attribute name from __set_name__
Available keys at 'database': ['host', 'port', 'name']
Hint: Check your config files or add default= parameter
```

### No Caching Rationale

ConfigValue intentionally does NOT cache resolved values:

**Why not cache?**
1. **Test refresh**: Descriptors would see stale values after `reload_for_testing()`
2. **Cache invalidation**: Complex logic to invalidate on config changes
3. **Memory overhead**: Each instance needs separate cache
4. **Low access cost**: ConfigSingleton.get() + dict lookup is ~1-2μs

**When caching matters:**
Use `@ConfigurationProperties` for grouping related config, or cache locally in hot loops:

```python
class Processor:
    batch_size: int = ConfigValue("processor.batch_size")

    def process_millions(self, items):
        batch_size = self.batch_size  # Cache in local variable
        for item in items:
            process(item, batch_size)  # Use cached value
```

---

## @ConfigurationProperties Decorator

### Decorator Pattern

@ConfigurationProperties wraps the class `__init__` method to inject attribute binding:

```python
def ConfigurationProperties(prefix: str):
    def decorator(cls):
        original_init = cls.__init__

        def __init__(self, *args, **kwargs):
            # 1. Call original __init__ (if user-defined)
            original_init(self, *args, **kwargs)

            # 2. Resolve config section
            cfg = ConfigSingleton.get()
            section = cfg.get(prefix)

            # 3. Store Config object
            self._config = Config(section)

            # 4. Auto-bind type-hinted attributes
            for attr_name, attr_type in cls.__annotations__.items():
                value = self._config.get(attr_name)

                # Handle nested objects
                if _is_config_class(attr_type):
                    value = attr_type()  # Recursive binding

                setattr(self, attr_name, value)

        cls.__init__ = __init__
        return cls

    return decorator
```

### Binding Flow

```
User: db = DatabaseConfig()
     ↓
Decorated __init__() called
     ↓
Call original __init__() (if present)
     ↓
ConfigSingleton.get() → Config instance
     ↓
Config.get("database") → section
     ↓
Store as self._config
     ↓
For each type-hinted attribute:
  ├─ Get value from section
  ├─ Is type hint a class? → Auto-instantiate (nested)
  ├─ Is value LazySecret? → Keep as-is
  └─ Convert type → setattr()
     ↓
Instance fully bound
```

### Nested Object Binding

Nested objects auto-instantiate when the type hint is a class (not a primitive):

```python
@ConfigurationProperties(prefix="app.database")
class DatabaseConfig:
    connection: ConnectionPoolConfig  # Type hint is a class

@ConfigurationProperties(prefix="connection")
class ConnectionPoolConfig:
    min_size: int
    max_size: int
```

**YAML Structure:**
```yaml
app:
  database:
    connection:
      min_size: 5
      max_size: 20
```

**Binding Flow:**
1. `DatabaseConfig.__init__()` called
2. Resolves `app.database` section
3. Finds `connection: {...}` in section
4. Detects `ConnectionPoolConfig` is a class (via `isinstance(attr_type, type)`)
5. Calls `ConnectionPoolConfig()` → recursively binds `min_size` and `max_size`
6. Assigns to `db.connection`

**Detection Logic:**
```python
def _is_config_class(type_hint) -> bool:
    """Check if type hint is a class (for nested object detection)."""
    return isinstance(type_hint, type) and type_hint not in (str, int, float, bool, list, dict)
```

### ._config Attribute

The decorator stores the original Config object as `._config` to provide an escape hatch:

```python
@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    host: str
    port: int

db = DatabaseConfig()
print(db.host)                   # Bound attribute
print(db._config.get("host"))    # Config object access
print(db._config.to_dict())      # Config method
db._config.dump("output.yml")    # Config method
```

This flexibility allows:
- Access to Config methods (`to_dict()`, `dump()`, etc.)
- Dotted-key access (`_config.get("nested.key")`)
- Debugging (inspect raw config structure)

### Preservation of Original __init__

The decorator respects user-defined `__init__` methods:

```python
@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    url: str
    port: int

    def __init__(self, override_port=None):
        # User logic here
        self.custom_field = "value"
        if override_port:
            self.port = override_port

# Decorator wraps this __init__:
# 1. Calls original __init__(self, override_port=...)
# 2. Then auto-binds url and port from config
# 3. User can override port via parameter
```

---

## @config_inject Decorator

### Signature Introspection

@config_inject uses `inspect.signature()` to introspect function parameters:

```python
def config_inject(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(func)  # Get parameter info

        # Build bound_args dict
        bound_args = {}

        # Bind positional args
        param_names = list(sig.parameters.keys())
        for i, arg in enumerate(args):
            if i < len(param_names):
                bound_args[param_names[i]] = arg

        # Bind keyword args (overrides positional)
        bound_args.update(kwargs)

        # Resolve ConfigValue defaults for missing parameters
        for param_name, param in sig.parameters.items():
            if param_name in bound_args:
                continue  # Already provided

            if isinstance(param.default, ConfigValue):
                resolved = param.default.__get__(None, None)
                bound_args[param_name] = resolved

        return func(**bound_args)

    return wrapper
```

### Override Semantics

Explicit arguments take precedence over config values:

```python
@config_inject
def connect(
    host: str = ConfigValue("db.host"),
    port: int = ConfigValue("db.port", default=5432),
    user: str = None
):
    pass

# Scenarios:
connect(user="admin")                    # Uses config for host/port
connect(user="admin", host="localhost")  # Overrides host
connect("admin", "localhost", 5432)      # All positional (overrides all)
```

**Resolution Order:**
1. Positional arguments → bound_args
2. Keyword arguments → bound_args (overrides positional)
3. ConfigValue defaults → bound_args (only if missing)
4. Regular defaults → bound_args (only if missing and not ConfigValue)

### Parameter Binding Flow

```
User: connect_db(user="admin")
     ↓
Wrapper function called with args=(), kwargs={"user": "admin"}
     ↓
inspect.signature(connect_db) → {host, port, user}
     ↓
Build bound_args:
  ├─ Positional args: none
  ├─ Keyword args: {"user": "admin"}
  └─ Missing params with ConfigValue:
      ├─ host: ConfigValue("db.host").__get__(None, None) → "localhost"
      ├─ port: ConfigValue("db.port").__get__(None, None) → 5432
      └─ user: already in bound_args
     ↓
connect_db(**bound_args) → connect_db(host="localhost", port=5432, user="admin")
```

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

### Bool Conversion

String-to-bool conversion is case-insensitive and supports common values:

```python
if target_type == bool:
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)
```

**Truthy strings**: `"true"`, `"True"`, `"TRUE"`, `"1"`, `"yes"`, `"on"`
**Falsy strings**: Anything else → `False`

### Special Cases

**LazySecret**: Never converted, always passed through unchanged

```python
if isinstance(value, LazySecret):
    return value  # No conversion
```

**Config**: Never converted, returned as Config instance

```python
if isinstance(value, Config):
    return value  # No conversion
```

**None/Missing**: Returns default or raises ConfigLoadError

```python
if value is None and self.default is None:
    raise ConfigLoadError(...)
```

### Conversion Errors

Type conversion failures raise `ConfigLoadError` with full context:

```python
try:
    converted = int(value)
except (ValueError, TypeError) as e:
    raise ConfigLoadError(
        f"Cannot convert config value to type 'int'\n"
        f"Key: database.port\n"
        f"Value: \"not_a_number\" (type: str)\n"
        f"Expected: int\n"
        f"Descriptor: ConfigValue('database.port') on MyService.db_port\n"
        f"Reason: invalid literal for int() with base 10: 'not_a_number'\n"
        f"Hint: Check your config file and ensure the value is a valid int"
    )
```

---

## LazySecret Integration

### Memory Layout

**decrypt=False (default)**:
```
Memory:
┌─────────────────┐
│ ConfigValue     │  (Descriptor instance, no data in obj.__dict__)
├─────────────────┤
│ LazySecret      │
│  _encrypted_value: "gAAA..."  (Fernet ciphertext)
│  _decrypted_value: None       (Not yet decrypted)
│  _key: "APP_SECRET_KEY"
└─────────────────┘
```

**After .get() called on LazySecret**:
```
Memory:
┌─────────────────┐
│ LazySecret      │
│  _encrypted_value: "gAAA..."
│  _decrypted_value: "actual_secret"  (Cached plaintext)
│  _key: "APP_SECRET_KEY"
└─────────────────┘
```

**decrypt=True**:
```
Memory:
┌─────────────────┐
│ ConfigValue     │  (Descriptor instance)
├─────────────────┤
│ str (in obj.__dict__)
│  "actual_secret"  (Plaintext immediately)
└─────────────────┘
```

### Security Trade-offs

| Approach | Memory State | Exposure Time | Use Case |
|----------|--------------|---------------|----------|
| `decrypt=False` | Encrypted | Minimal (only during .get()) | Rarely-accessed secrets (emergency keys) |
| `decrypt=True` | Plaintext | Entire instance lifetime | Frequently-used secrets (DB passwords) |
| Plaintext YAML | Plaintext | Forever | Non-secrets only |

### Decryption Error Handling

LazySecret decryption failures are wrapped with descriptor context:

```python
if self.decrypt:
    try:
        value = value.get()
    except Exception as e:
        raise ConfigLoadError(
            f"Failed to decrypt LazySecret for key '{self.key}'\n"
            f"Descriptor: ConfigValue('{self.key}', decrypt=True) on {self._owner_name}.{self._attr_name}\n"
            f"Reason: {e}\n"
            f"Hint: Check APP_SECRET_KEY environment variable"
        )
```

---

## Test-Only Refresh Mechanism

### ConfigValue Auto-Refresh

ConfigValue descriptors resolve from ConfigSingleton on every access:

```python
def __get__(self, obj, objtype=None):
    cfg = ConfigSingleton.get()  # Always reads current singleton
    value = cfg.get(self.key, self.default)
    # ...
```

**Refresh Behavior**:
```python
class Service:
    timeout: int = ConfigValue("service.timeout")

ConfigSingleton.initialize(profile="dev", ...)
service = Service()
print(service.timeout)  # 30 (from dev config)

reload_for_testing(profile="prod", ...)  # Clears + re-initializes singleton
print(service.timeout)  # 60 (from prod config) - auto-refreshed!
```

### @ConfigurationProperties Instance-Specific

Values bound at instantiation (stored in `__dict__`):

```python
@ConfigurationProperties(prefix="app")
class AppConfig:
    name: str

ConfigSingleton.initialize(profile="dev", ...)
app = AppConfig()
print(app.name)  # "dev-app"

reload_for_testing(profile="prod", ...)
print(app.name)  # "dev-app" (unchanged - old instance)

app_new = AppConfig()  # Create new instance
print(app_new.name)  # "prod-app" (reads from new singleton)
```

### @config_inject Per-Call Refresh

ConfigValue resolved on each function call:

```python
@config_inject
def connect(host: str = ConfigValue("db.host")):
    return host

ConfigSingleton.initialize(profile="dev", ...)
print(connect())  # "dev-host"

reload_for_testing(profile="prod", ...)
print(connect())  # "prod-host" - auto-refreshed!
```

---

## Error Handling Design

### Error Message Template

All ConfigLoadError messages follow this template:

```
ConfigLoadError: <brief description>
<Key/Value context>
<Location context (descriptor/class/function)>
Reason: <underlying error>
Hint: <actionable suggestion>
```

### Context Capture

**ConfigValue** captures context via `__set_name__`:
- `self._owner_name` - Class name
- `self._attr_name` - Attribute name
- Used in all error messages for clarity

**@ConfigurationProperties** captures context from decorator:
- `cls.__name__` - Class being decorated
- `prefix` - Config prefix
- Used in error messages

**@config_inject** captures context from function:
- `func.__name__` - Function name
- `param_name` - Parameter name
- Used in error messages

### Available Keys Hint

When a key is missing, ConfigValue tries to show available keys at the parent level:

```python
if value is None and self.default is None:
    key_parts = self.key.split(".")
    if len(key_parts) > 1:
        parent_key = ".".join(key_parts[:-1])
        parent = cfg.get(parent_key)
        if isinstance(parent, (dict, Config)):
            available = list(parent.keys())
            raise ConfigLoadError(
                f"Config key '{self.key}' not found and no default provided.\n"
                f"Available keys at '{parent_key}': {available}\n"
                f"Hint: Check your config files or add default= parameter"
            )
```

**Example**:
```
ConfigLoadError: Config key 'database.url' not found and no default provided.
Descriptor: ConfigValue('database.url') on MyService.db_url
Available keys at 'database': ['host', 'port', 'name']  # <-- Helpful!
Hint: Check your config files or add default= parameter
```

---

## Performance Characteristics

### ConfigValue Overhead

**Per-Access Cost**: ~1-2μs
- ConfigSingleton.get(): ~0.5μs (dict lookup)
- Config.get(key): ~0.5μs (dotted key resolution)
- Type conversion: ~0.2-0.5μs
- LazySecret check: ~0.1μs

**When it matters**: Hot loops with millions of iterations

**Solution**: Cache in local variable
```python
batch_size = self.batch_size  # Cache once
for i in range(1000000):
    process(item, batch_size)  # Use cached value
```

### @ConfigurationProperties Overhead

**Instantiation Cost**: ~10-50μs (one-time)
- Depends on number of attributes
- Includes nested object instantiation

**Per-Access Cost**: 0μs
- Direct attribute access (`obj.attr`)
- Values stored in instance `__dict__`

**Best for**: Grouped config that doesn't change

### @config_inject Overhead

**Per-Call Cost**: ~5-10μs
- Signature introspection: ~2-3μs (cached by Python)
- Parameter binding: ~2-3μs
- ConfigValue resolution: ~1-2μs per parameter

**When it matters**: Functions called thousands of times per second

**Solution**: Call function once, cache result if possible

---

## Thread Safety

### ConfigValue

Thread-safe because:
- No descriptor-level state (only class-level attributes)
- ConfigSingleton.get() is thread-safe
- No shared mutable state

Multiple threads can access ConfigValue attributes concurrently.

### @ConfigurationProperties

Thread-safe because:
- Instance `__dict__` not shared across threads
- ConfigSingleton.get() called during `__init__` (thread-safe)
- No shared mutable state

Multiple threads can instantiate classes concurrently.

### @config_inject

Thread-safe because:
- `inspect.signature()` cached by Python (thread-safe)
- ConfigValue resolution per-call (thread-safe)
- No shared mutable state

Multiple threads can call decorated functions concurrently.

### Test Reload Thread Safety

**Caution**: `reload_for_testing()` is NOT thread-safe
- Uses `ConfigSingleton._clear_all()` (no lock)
- Only safe in single-threaded tests
- Must use `pytest -n 0` (no xdist parallelization) for refresh tests

---

## Integration with Existing SprigConfig

### No Changes to Core Modules

**Unchanged**:
- `config.py` - Config class
- `config_singleton.py` - Singleton pattern
- `config_loader.py` - Loading and merging
- `lazy_secret.py` - Secret handling
- `deepmerge.py` - Deep merge logic

**Additive Only**:
- `injection.py` - NEW module (this file)
- `__init__.py` - Add exports

### Public API Exports

Required changes to `__init__.py`:

```python
from .injection import (
    ConfigValue,
    ConfigurationProperties,
    config_inject,
)

__all__ = [
    # Existing...
    "Config",
    "ConfigLoader",
    "ConfigSingleton",
    # NEW: Dependency injection
    "ConfigValue",
    "ConfigurationProperties",
    "config_inject",
]
```

### Backward Compatibility

Existing code continues to work unchanged:

```python
# OLD WAY (still supported forever)
cfg = ConfigSingleton.get()
db_url = cfg.get("database.url")

# NEW WAY (opt-in)
class Service:
    db_url: str = ConfigValue("database.url")
```

---

## Design Rationale

### Why Descriptors for ConfigValue?

**Alternatives Considered**:

1. **Property Factory** - Rejected (no type hints, no `__set_name__`)
2. **Cached Attributes** - Rejected (no auto-refresh, verbose)
3. **Descriptor (Chosen)** - Type hint capture, lazy resolution, Pythonic

### Why Decorator for @ConfigurationProperties?

**Alternatives Considered**:

1. **Base Class** - Rejected (forces inheritance)
2. **Metaclass** - Rejected (too magical)
3. **Decorator (Chosen)** - Non-invasive, clear intent, flexible

### Why inspect.signature for @config_inject?

**Alternatives Considered**:

1. **Manual Argument Parsing** - Rejected (error-prone)
2. **inspect.signature (Chosen)** - Handles all cases, Pythonic

---

## Future Enhancements (Out of Scope)

- Validation framework (`@Min`, `@Max`, `@Pattern`)
- Complex type hints (`list[str]`, `Optional[str]`)
- Production reload (file watcher, hot reload)
- Nested binding enhancements (`list[NestedConfig]`)
- Performance optimizations (optional caching mode)

---

## Summary

The injection module provides three complementary patterns for config binding:

1. **ConfigValue** - Fine-grained control, lazy resolution, auto-refresh
2. **@ConfigurationProperties** - Batch binding, nested objects, ._config access
3. **@config_inject** - Function-level DI, override support

All patterns prioritize:
- Security (zero-trust LazySecret handling)
- Simplicity (type conversion only)
- Clarity (rich error messages)
- Compatibility (Config.get() unchanged)
- Testability (test-only refresh)
