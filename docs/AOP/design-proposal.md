# AOP Design Proposal: Spring Boot-Style Configuration Injection

## Overview

This proposal adds Spring Boot-inspired annotation-based configuration injection to SprigConfig, supporting three key patterns while maintaining backward compatibility with `Config.get()`.

## Use Cases

### 1. Class-Level Binding (`@ConfigurationProperties`)

Bind an entire config section to a class:

```python
from sprigconfig import ConfigurationProperties

@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    host: str
    port: int
    username: str
    password: str  # Can be LazySecret
    max_connections: int = 10  # Default value

# Usage
db = DatabaseConfig()
print(db.host)  # Auto-populated from database.host
print(db.port)  # Auto-populated from database.port
```

**application.yml:**
```yaml
database:
  host: localhost
  port: 5432
  username: admin
  password: ENC(...)
  max_connections: 20
```

### 2. Instance Variable Injection (`@Value` on fields)

Inject specific config values into class attributes:

```python
from sprigconfig import ConfigValue

class SomeService:
    def __init__(self):
        self.url = ConfigValue("database.url")
        self.timeout = ConfigValue("api.timeout", default=30, type=int)
        self.api_key = ConfigValue("api.key")  # Can be LazySecret

    def connect(self):
        # self.url resolves lazily on access
        connection = connect(self.url.get())
```

Or use descriptor syntax for class-level declarations:

```python
class SomeService:
    url: str = ConfigValue("database.url")
    timeout: int = ConfigValue("api.timeout", default=30)

    def connect(self):
        connection = connect(self.url)  # Auto-resolves
```

### 3. Function/Method Parameter Injection

Inject config values as function parameters:

```python
from sprigconfig import config_inject

@config_inject
def connect_db(
    host: str = ConfigValue("database.host"),
    port: int = ConfigValue("database.port"),
    username: str = ConfigValue("database.username")
):
    """Parameters auto-injected at call time."""
    return f"Connecting to {host}:{port} as {username}"

# Call without arguments - values injected from config
connect_db()

# Or override specific values
connect_db(host="prod-db.example.com")
```

## Implementation Design

### Core Components

#### 1. `ConfigValue` - Lazy Value Descriptor

```python
class ConfigValue:
    """
    Descriptor that lazily resolves config values at access time.
    Supports type conversion via type hints.
    """
    def __init__(self, key: str, *, default=None, type=None):
        self.key = key
        self.default = default
        self.type = type

    def __get__(self, obj, objtype=None):
        """Resolve from config at access time."""
        from .config_singleton import get_config

        value = get_config().get(self.key, self.default)

        # Handle LazySecret - keep it lazy
        if isinstance(value, LazySecret):
            return value

        # Type conversion if specified
        if self.type is not None and value is not None:
            return self.type(value)

        return value

    def __set__(self, obj, value):
        """Prevent overwriting descriptor."""
        raise AttributeError(f"Cannot set config value '{self.key}'")
```

#### 2. `@ConfigurationProperties` - Class Binding

```python
def ConfigurationProperties(prefix: str = ""):
    """
    Class decorator that auto-populates annotated fields from config.
    Similar to Spring Boot's @ConfigurationProperties.
    """
    def decorator(cls):
        original_init = cls.__init__

        def new_init(self, *args, **kwargs):
            # Call original __init__ first
            original_init(self, *args, **kwargs)

            # Auto-populate from config
            from .config_singleton import get_config
            config = get_config()

            # Get the config section for this prefix
            if prefix:
                section = config.get(prefix, {})
            else:
                section = config

            # Populate annotated fields
            for field_name, field_type in cls.__annotations__.items():
                config_key = f"{prefix}.{field_name}" if prefix else field_name

                # Check if field has default value
                default = getattr(cls, field_name, None)

                # Get value from config
                if prefix:
                    value = section.get(field_name, default)
                else:
                    value = config.get(field_name, default)

                # Type conversion (if not LazySecret)
                if value is not None and not isinstance(value, LazySecret):
                    value = _convert_type(value, field_type)

                setattr(self, field_name, value)

        cls.__init__ = new_init
        return cls

    return decorator
```

#### 3. `@config_inject` - Function Parameter Injection

```python
def config_inject(func):
    """
    Decorator that injects ConfigValue defaults into function parameters.
    Similar to Spring's @Value on method parameters.
    """
    import inspect
    from functools import wraps

    sig = inspect.signature(func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Build bound arguments
        bound = sig.bind_partial(*args, **kwargs)

        # Inject missing parameters from ConfigValue defaults
        for param_name, param in sig.parameters.items():
            if param_name not in bound.arguments:
                if isinstance(param.default, ConfigValue):
                    # Resolve the ConfigValue
                    injected_value = param.default.__get__(None, None)
                    bound.arguments[param_name] = injected_value

        return func(**bound.arguments)

    return wrapper
```

## Type Conversion

The system should automatically convert config values based on type hints:

```python
class AppConfig:
    port: int          # Auto-convert from YAML string/int
    debug: bool        # Auto-convert from YAML true/false
    timeout: float     # Auto-convert to float
    tags: list[str]    # Keep as list (YAML sequence)
```

**Conversion rules:**
1. Primitives (int, str, float, bool) - standard Python conversion
2. `LazySecret` - always preserved (no conversion)
3. Complex types (list, dict) - no conversion, pass through
4. Missing values with defaults - use default
5. Missing values without defaults - raise `ConfigLoadError`

## LazySecret Handling

Secrets remain lazy across all injection mechanisms:

```python
@ConfigurationProperties(prefix="api")
class APIConfig:
    url: str
    secret_key: str  # Will be LazySecret if value is ENC(...)

api = APIConfig()
print(api.url)         # "https://api.example.com"
print(api.secret_key)  # <LazySecret object>

# Explicit resolution required
actual_key = api.secret_key.get()  # Decrypts on demand
```

## Error Handling

### Missing Required Values

```python
@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    host: str  # No default - REQUIRED
    port: int = 5432  # Has default - optional

# Raises ConfigLoadError if database.host is missing
db = DatabaseConfig()
```

### Invalid Type Conversion

```python
class AppConfig:
    port: int = ConfigValue("server.port")

# application.yml: server.port: "not-a-number"
# Raises ConfigLoadError: "Cannot convert 'not-a-number' to int for key 'server.port'"
```

## Profile-Aware Binding

All injection mechanisms respect the active profile:

```python
config = load_config(profile="prod")

@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    host: str

# Automatically uses values from application-prod.yml
db = DatabaseConfig()
```

## Integration with Existing Config

The annotation system is **additive** - `Config.get()` continues to work:

```python
# Traditional approach - still supported
config = load_config()
db_host = config.get("database.host")

# New approach - annotation-based
@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    host: str

db = DatabaseConfig()
```

Both approaches use the same underlying config singleton.

## Implementation Phases

### Phase 1: Core Descriptors
- Implement `ConfigValue` descriptor
- Add basic type conversion
- LazySecret preservation

### Phase 2: Class Binding
- Implement `@ConfigurationProperties`
- Type hint introspection
- Default value handling

### Phase 3: Function Injection
- Implement `@config_inject`
- Parameter introspection
- Argument binding

### Phase 4: Advanced Features
- Nested object binding
- Collection type conversion
- Validation integration (future: JSR-303 style)

## Testing Strategy

### Unit Tests
- `test_config_value_descriptor.py` - Descriptor behavior
- `test_configuration_properties.py` - Class binding
- `test_config_inject.py` - Function injection
- `test_type_conversion.py` - Type conversion logic

### Integration Tests
- `test_aop_with_profiles.py` - Profile overlay behavior
- `test_aop_lazy_secrets.py` - LazySecret preservation
- `test_aop_errors.py` - Error conditions

## Documentation Requirements

1. **User Guide**: `docs/configuration-injection.md`
2. **Migration Guide**: How to adopt annotations in existing projects
3. **API Reference**: All decorators and descriptors
4. **Examples**: Real-world use cases

## Backward Compatibility

**Guaranteed:**
- `Config.get()` continues to work exactly as before
- `load_config()` API unchanged
- Existing code requires zero changes

**New features are opt-in:**
- Import annotations explicitly: `from sprigconfig import ConfigValue`
- No runtime overhead if not used

## Open Questions

1. **Validation**: Should we support validation annotations (e.g., `@Min`, `@Max`)?
2. **Refresh**: Should bound values update if `load_config()` is called again?
3. **Frozen Classes**: Should `@ConfigurationProperties` support `@dataclass(frozen=True)`?
4. **Nested Binding**: Should nested classes auto-bind? E.g.:
   ```python
   class DatabaseConfig:
       connection: ConnectionPoolConfig  # Auto-bind nested object?
   ```

## Next Steps

1. Review and refine this proposal
2. Create prototype implementation in feature branch
3. Write comprehensive tests
4. Update documentation
5. Add examples to README
