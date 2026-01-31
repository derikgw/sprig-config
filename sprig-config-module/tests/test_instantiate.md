# test_instantiate.md

## Overview

Comprehensive test suite for SprigConfig's `_target_` dynamic class instantiation feature introduced in v1.4.0. Tests Hydra-style class instantiation from configuration.

## Test Coverage

### Real Config File Tests

| Test Class | Purpose |
|------------|---------|
| `TestInstantiateWithRealConfigs` | Tests instantiation from YAML, JSON, and TOML config files |

Verifies format-agnostic behavior using `tests/config/targets/` configs.

### Integration with @config_inject

| Test Class | Purpose |
|------------|---------|
| `TestInstantiateWithConfigInject` | Verifies instantiated objects work with @config_inject |

Tests that `MSSQLDatabase.connect()` (which uses @config_inject) works after instantiation.

### Basic Instantiation

| Test Class | Purpose |
|------------|---------|
| `TestInstantiateBasic` | Simple instantiation, optional parameters, default values |

### Type Conversion

| Test Class | Purpose |
|------------|---------|
| `TestInstantiateTypeConversion` | int, float, bool conversion during instantiation |

### Recursive Instantiation

| Test Class | Purpose |
|------------|---------|
| `TestInstantiateRecursive` | Nested `_target_` objects, `_recursive_=False` option |

### Error Handling

| Test Class | Purpose |
|------------|---------|
| `TestInstantiateErrors` | Missing _target_, invalid format, module not found, class not found, missing required params, type conversion errors |

### Edge Cases

| Test Class | Purpose |
|------------|---------|
| `TestInstantiateEdgeCases` | Invalid config types, empty config, `_convert_types_=False` |

## Test Helper Classes

The test file defines several helper classes for testing:

```python
class SimpleAdapter:
    """Simple adapter with required parameters."""
    def __init__(self, url: str, port: int): ...

class OptionalParamsAdapter:
    """Adapter with optional parameters."""
    def __init__(self, url: str, port: int = 5432, timeout: float = 30.0): ...

class BooleanAdapter:
    """Adapter that accepts boolean parameters."""
    def __init__(self, enabled: bool, debug: bool = False): ...

class NestedAdapter:
    """Adapter that accepts another adapter as parameter."""
    def __init__(self, database: SimpleAdapter, name: str): ...
```

## Key Scenarios Covered

1. **Multi-format support** - YAML, JSON, TOML all work identically
2. **Type conversion** - Automatic conversion based on `__init__` type hints
3. **Recursive instantiation** - Nested `_target_` objects are instantiated
4. **Optional parameters** - Constructor defaults are respected
5. **@config_inject integration** - Instantiated objects can use DI decorators
6. **Error messages** - Clear errors for all failure modes

## Config File Structure

Tests use real config files in `tests/config/`:

```
tests/config/
├── application-target-test.yml
├── application-target-test.json
├── application-target-test.toml
└── targets/
    └── ... (adapter definitions)
```

## Running Tests

```bash
# Run all instantiate tests
poetry run pytest tests/test_instantiate.py -v

# Run specific test class
poetry run pytest tests/test_instantiate.py::TestInstantiateWithRealConfigs -v

# Run with coverage
poetry run pytest tests/test_instantiate.py --cov=src/sprigconfig/instantiate
```

## Dependencies

- `tests/db/mssql/mssql_database_adapter.py` - Real adapter for integration tests
- `tests/config/` - Config files with `_target_` definitions
- ConfigSingleton for @config_inject integration tests
