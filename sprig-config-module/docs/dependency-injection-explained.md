# Dependency Injection - Implementation Explained

This document explains **exactly** how SprigConfig's Spring Boot-style dependency injection works, step by step, assuming no prior knowledge.

## Table of Contents

1. [Overview](#overview)
2. [Pattern 1: ConfigValue Descriptor](#pattern-1-configvalue-descriptor)
3. [Pattern 2: @ConfigurationProperties Decorator](#pattern-2-configurationproperties-decorator)
4. [When to Use Each Pattern](#when-to-use-each-pattern)

---

## Overview

SprigConfig provides two patterns for injecting configuration into your classes. Both accomplish the same goal (getting config values into your classes), but they do it differently.

**The Goal:** Turn this config YAML:
```yaml
database:
  host: localhost
  port: 5432
```

Into this Python code:
```python
db = DatabaseConfig()
print(db.host)  # "localhost"
print(db.port)  # 5432
```

Without manually calling `config.get("database.host")` everywhere.

---

## Pattern 1: ConfigValue Descriptor

### What You Write

```python
class DatabaseService:
    host: str = ConfigValue("database.host")
    port: int = ConfigValue("database.port")

# Usage
db = DatabaseService()
print(db.host)  # Resolves from config
```

### How It Works (The Magic Explained)

This uses Python's **descriptor protocol**. Here's what happens step by step:

#### Step 1: Class Definition Time

When Python sees this:
```python
class DatabaseService:
    host: str = ConfigValue("database.host")
```

Python does the following:
1. Creates a `ConfigValue` object with `key="database.host"`
2. Assigns it to the class attribute `DatabaseService.host`
3. **Automatically calls** `ConfigValue.__set_name__(DatabaseService, "host")`

The `__set_name__` method captures important information:
```python
def __set_name__(self, owner, name):
    self._owner_name = "DatabaseService"  # Class name
    self._attr_name = "host"              # Attribute name
    self._type_hint = str                 # From type annotation
```

So the `ConfigValue` object now "knows" it belongs to `DatabaseService.host` and expects a `str`.

#### Step 2: Instance Creation

When you create an instance:
```python
db = DatabaseService()
```

Nothing special happens yet. The instance is created normally.

#### Step 3: Attribute Access

When you access the attribute:
```python
print(db.host)
```

Python's descriptor protocol kicks in:

1. Python sees you're accessing `db.host`
2. Python checks: "Is `DatabaseService.host` a descriptor?" → YES (it has `__get__`)
3. Python calls: `ConfigValue.__get__(db, DatabaseService)`

Inside `__get__`, this happens:
```python
def __get__(self, obj, objtype=None):
    # 1. Get the global config
    cfg = ConfigSingleton.get()

    # 2. Look up the value using the key we stored
    value = cfg.get("database.host")  # Returns "localhost"

    # 3. Convert to the expected type (str)
    if self._type_hint:
        value = self._convert_type(value, str)

    # 4. Return the value
    return value  # "localhost"
```

**Result:** Every time you access `db.host`, it fetches the latest value from config and converts it to the right type.

### Key Points

- **Lazy evaluation:** Config is fetched every time you access the attribute (no caching)
- **Type conversion:** Automatically converts YAML values to Python types
- **Error handling:** Clear messages if config key is missing
- **Read-only:** You can't do `db.host = "something"` (raises error)

---

## Pattern 2: @ConfigurationProperties Decorator

### What You Write

```python
@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    host: str
    port: int
    name: str

# Usage
db = DatabaseConfig()
print(db.host)  # Resolves from config
```

### How It Works (The Magic Explained)

This pattern is completely different. Instead of descriptors, it uses **`__init__` injection**.

#### Step 1: Class Definition Time

When Python processes:
```python
@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    host: str
    port: int
```

The decorator runs:
```python
def ConfigurationProperties(prefix):
    def decorator(cls):
        # Save the original __init__ (if any)
        original_init = cls.__init__

        # Define a NEW __init__ that does config binding
        def __init__(self, *args, **kwargs):
            # 1. Call original __init__ if user defined one
            if original_init != object.__init__:
                original_init(self, *args, **kwargs)

            # 2. Get config from singleton
            cfg = ConfigSingleton.get()

            # 3. Get the config section for this prefix
            section = cfg.get("database")
            # section = {"host": "localhost", "port": 5432, "name": "mydb"}

            # 4. Store as _config attribute
            self._config = Config(section)

            # 5. Auto-bind all type-annotated attributes
            for attr_name, attr_type in cls.__annotations__.items():
                # attr_name = "host", attr_type = str
                # attr_name = "port", attr_type = int
                # attr_name = "name", attr_type = str

                # Get the value from config section
                value = self._config.get(attr_name)
                # For "host" → value = "localhost"
                # For "port" → value = 5432

                # Convert type if needed
                converted = _convert_type_for_properties(value, attr_type, ...)

                # Set as instance attribute
                setattr(self, attr_name, converted)
                # self.host = "localhost"
                # self.port = 5432

        # Replace the class's __init__ with our new one
        cls.__init__ = __init__
        return cls

    return decorator
```

#### Step 2: Instance Creation

When you create an instance:
```python
db = DatabaseConfig()
```

Our custom `__init__` runs:
1. Fetches config section `database` from ConfigSingleton
2. Loops through all type annotations (`host: str`, `port: int`, `name: str`)
3. Gets each value from the config section
4. Converts to the annotated type
5. Sets as instance attributes

**After `__init__` completes:**
```python
db.host = "localhost"  # Plain string attribute
db.port = 5432         # Plain int attribute
db.name = "mydb"       # Plain string attribute
```

#### Step 3: Attribute Access

When you access:
```python
print(db.host)
```

This is just a **normal attribute access**. No descriptor, no magic. It's a regular Python attribute.

### Key Differences from Pattern 1

| Aspect | ConfigValue (Pattern 1) | @ConfigurationProperties (Pattern 2) |
|--------|-------------------------|--------------------------------------|
| When resolved | Every access (lazy) | Once at `__init__` (eager) |
| Storage | No instance attribute | Instance attribute |
| Descriptor? | Yes | No |
| Updates | Always fresh | Static after creation |
| Best for | Individual fields | Whole config sections |

### Key Points

- **Eager evaluation:** Config is fetched once during `__init__`
- **Instance attributes:** Values are stored as regular attributes
- **Section binding:** Binds an entire config section at once
- **Nested support:** Can auto-instantiate nested config objects
- **Static after init:** Values don't update if config changes

---

## When to Use Each Pattern

### Use ConfigValue (Pattern 1) When:
```python
class MyService:
    url: str = ConfigValue("api.url")
    timeout: int = ConfigValue("api.timeout", default=30)
```
- You need **a few scattered config values** from different sections
- You want **lazy evaluation** (always fetch latest value)
- You want config changes to be reflected immediately

### Use @ConfigurationProperties (Pattern 2) When:
```python
@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    host: str
    port: int
```
- You want to **bind an entire config section**
- The section has **many related fields**
- You want **better performance** (one-time binding)
- You don't need config to update after initialization
- You want Spring Boot-style section binding

---

## Complete Example Using Both Patterns

```python
from sprigconfig import (
    ConfigSingleton,
    ConfigValue,
    ConfigurationProperties
)

# Initialize ONCE at startup
ConfigSingleton.initialize(profile="dev", config_dir="./config")


# Pattern 1: ConfigValue (lazy, individual fields)
class CacheService:
    ttl: int = ConfigValue("cache.ttl", default=300)
    max_size: int = ConfigValue("cache.max_size", default=1000)


# Pattern 2: @ConfigurationProperties (eager, whole section)
@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    host: str
    port: int
    username: str
    password: str  # Could be LazySecret if encrypted


# Usage
cache = CacheService()
print(cache.ttl)  # Lazy: fetches from config each time

db = DatabaseConfig()
print(db.host)  # Eager: was set during __init__
```

---

## Common Questions

### Q: Why does Pattern 1 fetch on every access?

**A:** This enables config changes to be reflected immediately in tests. If you reinitialize ConfigSingleton with a different profile, the next access gets fresh data.

### Q: Why doesn't Pattern 2 update after initialization?

**A:** Pattern 2 stores values as plain instance attributes, so they're "frozen" after `__init__`. This is actually more efficient for production use where config doesn't change.

### Q: Can I mix both patterns?

**A:** Yes! They're completely independent. Use whichever makes sense for each class.

### Q: Which pattern is most like Spring Boot?

**A:** Pattern 2 (`@ConfigurationProperties`) is nearly identical to Spring Boot's `@ConfigurationProperties`. Pattern 1 is similar to Spring Boot's `@Value` but uses assignment syntax instead of field decorators (Python limitation).

### Q: Why can't I use decorators on fields like Spring Boot's @Value?

**A:** Python's decorator syntax only works on classes and functions, not field annotations. This is a fundamental limitation of Python's syntax. The assignment syntax (`field = ConfigValue(...)`) is the most Pythonic alternative.

---

## Terminology Clarification

**Annotations vs Decorators:**
- In **Python**, "annotations" refers to type hints: `name: str`
- In **Java/Spring Boot**, "annotations" are metadata markers: `@Value`, `@Component`
- What we call "decorators" in Python (`@ConfigurationProperties`) are similar to Java annotations
- SprigConfig uses **dependency injection** with Python **descriptors** and **decorators**

---

## Summary

| Pattern | Syntax | When Resolved | Best For |
|---------|--------|---------------|----------|
| 1. ConfigValue | `field = ConfigValue(...)` | Every access (lazy) | Few scattered values |
| 2. @ConfigurationProperties | `@ConfigurationProperties(prefix=...)` | Once at init (eager) | Whole sections |

Both patterns work together seamlessly. Choose based on your use case:
- **ConfigValue** for flexibility and individual fields
- **@ConfigurationProperties** for performance and section binding
