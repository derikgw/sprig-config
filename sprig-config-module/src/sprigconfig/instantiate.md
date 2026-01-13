# Dynamic Class Instantiation (`_target_` Support)

## Overview

SprigConfig supports Hydra-style `_target_` for dynamic class instantiation from configuration. This enables powerful patterns like hexagonal architecture with swappable adapters, perfect for:

- **Adapter Pattern**: Swap database or API implementations via config
- **Dependency Injection**: Wire up services without hardcoding class names
- **Profile-Specific Implementations**: Use SQLite in dev, PostgreSQL in prod
- **Plugin Architecture**: Load different implementations for different tenants

## Basic Usage

### Configuration

```yaml
# config/application.yml
adapters:
  database:
    _target_: myapp.adapters.postgres.PostgresAdapter
    host: localhost
    port: 5432
    pool_size: 10
```

### Python Code

```python
from sprigconfig import ConfigSingleton, instantiate

cfg = ConfigSingleton.get()

# Instantiate from config
db_adapter = instantiate(cfg.adapters.database)

# Use the adapter
db_adapter.connect()  # Calls PostgresAdapter.connect()
```

## How It Works

### 1. Detecting `_target_`

The `instantiate()` function looks for a `_target_` key in the config section:

```yaml
section:
  _target_: my.module.MyClass  # Full path to class
  param1: value1
  param2: value2
```

The `_target_` value must be a fully-qualified class path: `module.submodule.ClassName`

### 2. Dynamic Import

The module and class are imported dynamically:

```python
import importlib

module_path, class_name = "_target_".rsplit(".", 1)  # Split on last dot
module = importlib.import_module(module_path)         # Import module
target_class = getattr(module, class_name)            # Get class from module
```

### 3. Parameter Extraction

The function inspects the class's `__init__` signature and extracts matching parameters:

```python
import inspect

sig = inspect.signature(MyClass.__init__)

# For each parameter in __init__ (except 'self'):
#   - If the parameter exists in config, use that value
#   - If the parameter is required (no default) and missing, raise an error
#   - If the parameter is optional and missing, use the constructor default
```

Example:

```python
class MyAdapter:
    def __init__(self, host: str, port: int, timeout: float = 30.0):
        ...

# Config with only 'host' and 'port' - 'timeout' uses default
config = {
    "_target_": "my.module.MyAdapter",
    "host": "localhost",
    "port": 5432,
    # timeout not specified, uses default 30.0
}
```

### 4. Type Conversion

Type hints are used to convert config values to the correct types:

```python
# Config (strings from YAML)
config = {
    "_target_": "my.module.MyClass",
    "count": "42",          # String in YAML
    "enabled": "true",      # String in YAML
    "timeout": "3.14",      # String in YAML
}

# After type conversion:
instance = MyClass(
    count=42,               # int (converted from "42")
    enabled=True,           # bool (converted from "true")
    timeout=3.14            # float (converted from "3.14")
)
```

**Supported Conversions:**
- `str` → string cast
- `int` → integer parse
- `float` → float parse
- `bool` → boolean parse ("true", "1", "yes", "on" → True)
- `list` → list preservation (no conversion)
- `dict` → dict preservation (no conversion)
- `LazySecret` → pass through unchanged
- `Config` → pass through unchanged

### 5. Instantiation

Once parameters are prepared, the class is instantiated:

```python
instance = target_class(**init_params)
```

## Features

### Recursive Instantiation

If a constructor parameter value contains `_target_`, it's recursively instantiated:

```yaml
app:
  database:
    _target_: myapp.adapters.PostgresAdapter
    pool:
      _target_: myapp.pool.ConnectionPool
      size: 10
      timeout: 30
```

```python
cfg = ConfigSingleton.get()
app = instantiate(cfg.app)

# Both database and pool are instantiated:
# app.database = PostgresAdapter(pool=ConnectionPool(size=10, timeout=30))
```

**Disable recursion** with `_recursive_=False`:

```python
adapter = instantiate(cfg.database, _recursive_=False)
# Nested _target_ dicts are passed as-is (not instantiated)
```

### Type Conversion Control

Type conversion can be disabled with `_convert_types_=False`:

```python
# Normally type conversion happens
result = instantiate(config)           # port="5432" → port=5432 (int)

# Disable type conversion
result = instantiate(config, _convert_types_=False)  # port stays as "5432"
```

### LazySecret Handling

LazySecrets (encrypted config values) are preserved:

```python
config = {
    "_target_": "myapp.Database",
    "password": LazySecret(...)  # Encrypted secret
}

# The LazySecret is passed as-is to the constructor
# The constructor can call .get() to decrypt it
```

## Hexagonal Architecture Example

Perfect for implementing the hexagonal (ports/adapters) pattern:

### Config

```yaml
# config/application.yml
core:
  auth_port: auth
  database_port: database

adapters:
  auth:
    _target_: myapp.adapters.oauth.OAuthAdapter
    client_id: ${env:OAUTH_CLIENT_ID}
    client_secret: ${secrets.oauth_secret}

  database:
    _target_: myapp.adapters.postgres.PostgresAdapter
    host: localhost
    port: 5432
```

### Code

```python
from sprigconfig import ConfigSingleton, instantiate

cfg = ConfigSingleton.get()

# Instantiate adapters
auth_adapter = instantiate(cfg.adapters.auth)
db_adapter = instantiate(cfg.adapters.database)

# Wire up core application
app = MyApplication(
    auth=auth_adapter,
    database=db_adapter
)
```

### Profile-Specific Adapters

```yaml
# config/application-dev.yml
adapters:
  database:
    _target_: myapp.adapters.sqlite.SqliteAdapter
    file: /tmp/dev.db

# config/application-prod.yml
adapters:
  database:
    _target_: myapp.adapters.postgres.PostgresAdapter
    host: prod-db.example.com
    port: 5432
```

At runtime, the correct adapter is loaded based on the profile!

## Error Handling

Clear, actionable error messages with context:

```python
config = {
    "_target_": "nonexistent.Module",
    "param": "value"
}

instantiate(config)
# ConfigLoadError: Module not found for _target_: 'nonexistent.Module'
# Module path: 'nonexistent'
# Reason: No module named 'nonexistent'
# Hint: Check that the module is installed and importable
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `No _target_ key found` | Missing `_target_` in config | Add `_target_: your.module.Class` |
| `Invalid _target_ format` | `_target_` has no dots | Use `module.submodule.ClassName` |
| `Module not found` | Module doesn't exist | Check module path and spelling |
| `Class not found in module` | Class not defined in module | Check class name and spelling |
| `Missing required parameters` | Constructor param missing from config | Add parameter to config section |
| `Failed to convert parameter` | Type conversion failed | Check config value type |

## API Reference

### `instantiate(config_section, *, _recursive_=True, _convert_types_=True)`

Instantiate a class from config using `_target_` key.

**Parameters:**
- `config_section` (Config or dict): Config with `_target_` key
- `_recursive_` (bool): Recursively instantiate nested `_target_` objects (default: True)
- `_convert_types_` (bool): Apply type conversion to constructor params (default: True)

**Returns:**
- Instance of the class specified by `_target_`

**Raises:**
- `ConfigLoadError`: If `_target_` missing, class not found, invalid format, missing required params, or instantiation fails

**Example:**

```python
from sprigconfig import ConfigSingleton, instantiate

cfg = ConfigSingleton.get()
adapter = instantiate(cfg.adapters.database)
```

## Design Notes

### Why `_target_` and Not XML/JSON?

- `_target_` follows Hydra convention (widely recognized in ML/Python community)
- Minimal overhead: just a string key in config
- Works with any config format (YAML, JSON, TOML)
- Backward compatible: `_target_` is just another key if not used with `instantiate()`

### Type Safety

Type conversion is based on Python type hints:

```python
def __init__(self, port: int):
    # Type hint tells instantiate() to convert to int
    self.port = port
```

If no type hint exists, the value is passed as-is:

```python
def __init__(self, port):  # No type hint
    # Value passed unchanged (stays as string if YAML)
    self.port = port
```

### Security

- **No arbitrary code execution**: Only class instantiation via `__init__`
- **LazySecret preservation**: Secrets stay encrypted until explicitly decrypted
- **Error messages safe**: Never log sensitive parameter values
- **Explicit import**: Only imports classes you specify in `_target_`

## Limitations & Future Work

### Current Limitations
- No support for factory methods (only `__init__`)
- No validation decorators yet (`@Min`, `@Max`, `@Pattern`)
- No circular reference detection

### Planned for Future
- `_partial_` for `functools.partial` behavior
- `_recursive_` depth limiting
- Validation framework
- Plugin registry for custom strategies

## Examples

### Example 1: Database Adapter Pattern

```yaml
# config/application.yml
database:
  _target_: app.adapters.DatabaseAdapter
  host: localhost
  port: 5432
  ssl: true
```

```python
from sprigconfig import ConfigSingleton, instantiate

cfg = ConfigSingleton.get()
db = instantiate(cfg.database)

# Works with @config_inject too!
@config_inject
def query(
    sql: str,
    pool_size: int = ConfigValue("database.pool_size", default=10)
):
    return db.query(sql, pool_size=pool_size)
```

### Example 2: Plugin System

```yaml
# config/application.yml
plugins:
  auth:
    _target_: plugins.auth.OAuthPlugin
    provider: google

  storage:
    _target_: plugins.storage.S3Plugin
    bucket: my-bucket
```

```python
cfg = ConfigSingleton.get()
plugins = {
    "auth": instantiate(cfg.plugins.auth),
    "storage": instantiate(cfg.plugins.storage),
}

for name, plugin in plugins.items():
    plugin.initialize()
```

### Example 3: Mixed DI Patterns

```python
# Use _target_ for adapter instantiation
adapter = instantiate(cfg.database)

# Use ConfigValue for application config
class AppConfig:
    debug: bool = ConfigValue("app.debug")
    log_level: str = ConfigValue("app.log_level")

# Use @config_inject for functions
@config_inject
def connect(
    timeout: int = ConfigValue("database.timeout")
):
    adapter.connect(timeout=timeout)
```

All three DI patterns work together seamlessly!
