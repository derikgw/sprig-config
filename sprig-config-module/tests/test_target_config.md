# test_target_config.md

## Overview

Quick smoke test to verify that the `MSSQLDatabase` adapter class can be instantiated directly. This is a minimal sanity check for the test infrastructure used by `test_instantiate.py`.

## Purpose

This test exists to:

1. **Verify test infrastructure** - Ensure `MSSQLDatabase` adapter is importable
2. **Quick sanity check** - Fast-running test to catch obvious issues
3. **Isolation** - Test the adapter class independently of `instantiate()`

## Test Coverage

| Test | Purpose |
|------|---------|
| `test_target_config` | Direct instantiation of MSSQLDatabase with required parameters |

## Code

```python
def test_target_config():
    """Test that MSSQLDatabase can be instantiated."""
    db = MSSQLDatabase(url="mssql://localhost", port=1234, database="test")

    assert db.url == "mssql://localhost"
    assert db.port == 1234
    assert db.database == "test"
```

## Relationship to Other Tests

This test complements `test_instantiate.py`:

- **test_target_config.py** - Tests direct instantiation (smoke test)
- **test_instantiate.py** - Tests `instantiate()` function with `_target_`

## Running Tests

```bash
# Run this specific test
poetry run pytest tests/test_target_config.py -v

# Run with instantiate tests
poetry run pytest tests/test_target_config.py tests/test_instantiate.py -v
```

## Dependencies

- `tests/db/mssql/mssql_database_adapter.py` - The MSSQLDatabase adapter class
