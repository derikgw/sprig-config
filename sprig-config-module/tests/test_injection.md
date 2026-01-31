# test_injection.md

## Overview

Comprehensive test suite for SprigConfig's dependency injection features. Tests all three DI patterns introduced in v1.3.0.

## Test Coverage

### ConfigValue Descriptor Tests

| Test Class | Purpose |
|------------|---------|
| `TestConfigValueBasicBinding` | String binding, nested keys, multiple fields, lazy evaluation |
| `TestConfigValueTypeConversion` | int, str, bool, float, list, dict conversions |
| `TestConfigValueDefaults` | Default values for missing keys |
| `TestConfigValueErrors` | Missing keys, uninitialized singleton, read-only, type errors |
| `TestConfigValueLazySecret` | LazySecret handling with decrypt=True/False |

### @ConfigurationProperties Tests

| Test Class | Purpose |
|------------|---------|
| `TestConfigurationPropertiesBasic` | Section binding, nested sections, ._config attribute |
| `TestConfigurationPropertiesTypeConversion` | Type conversion for bound attributes |
| `TestConfigurationPropertiesErrors` | Missing sections, non-dict sections |
| `TestConfigurationPropertiesPartialBinding` | Missing keys, custom __init__ |
| `TestConfigurationPropertiesLazySecret` | LazySecret preservation |

### @config_inject Tests

| Test Class | Purpose |
|------------|---------|
| `TestConfigInjectBasic` | Parameter injection, multiple parameters, regular defaults |
| `TestConfigInjectOverrides` | Keyword overrides, positional overrides, mixed |
| `TestConfigInjectErrors` | Missing config keys |

### Integration Tests

| Test Class | Purpose |
|------------|---------|
| `TestConfigValueResolveMethod` | resolve() method used by @config_inject |
| `TestConfigurationPropertiesNestedObjects` | Auto-instantiation of nested config classes |
| `TestDependencyInjectionIntegration` | All three patterns working together |

## Test Patterns

### Fixture Strategy

```python
@pytest.fixture(autouse=True)
def clear_singleton():
    """Clear singleton before and after each test."""
    ConfigSingleton._clear_all()
    yield
    ConfigSingleton._clear_all()
```

### Temporary Config Files

Many tests create temporary config directories to test specific scenarios:

```python
temp_dir = Path(tempfile.mkdtemp())
try:
    config_file = temp_dir / "application.yml"
    config_file.write_text("feature:\n  enabled: true\n")
    ConfigSingleton.initialize(profile="dev", config_dir=temp_dir)
    # ... test code ...
finally:
    shutil.rmtree(temp_dir)
```

### Error Testing

All error conditions are tested with clear assertions:

```python
with pytest.raises(ConfigLoadError) as exc_info:
    _ = service.missing

assert "does.not.exist" in str(exc_info.value)
assert "not found" in str(exc_info.value)
```

## Key Scenarios Covered

1. **Lazy resolution** - ConfigValue fetches fresh values on each access
2. **Type conversion** - Automatic conversion based on type hints
3. **LazySecret integration** - Encrypted secrets with decrypt parameter
4. **Error messages** - Clear, actionable error messages with context
5. **Read-only enforcement** - ConfigValue descriptors cannot be overwritten
6. **Nested binding** - @ConfigurationProperties with nested config classes
7. **Override semantics** - Explicit arguments take precedence over config

## Running Tests

```bash
# Run all injection tests
poetry run pytest tests/test_injection.py -v

# Run specific test class
poetry run pytest tests/test_injection.py::TestConfigValueBasicBinding -v

# Run with coverage
poetry run pytest tests/test_injection.py --cov=src/sprigconfig/injection
```

## Dependencies

- Uses `tests/config/` directory for real config files
- `use_real_config_dir` fixture from conftest.py
- ConfigSingleton must be cleared between tests
