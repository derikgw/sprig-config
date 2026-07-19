# Utilities API

## `deep_merge()`

`deep_merge(base, override)` recursively merges `override` into `base` and
returns the mutated `base` mapping.

```python
from sprigconfig import deep_merge

base = {"server": {"host": "localhost", "port": 8080}}
override = {"server": {"port": 9090}}

merged = deep_merge(base, override)
assert merged == {"server": {"host": "localhost", "port": 9090}}
```

Rules:

- dictionaries merge recursively;
- lists and scalar values replace earlier values;
- keys absent from the override are preserved;
- merge diagnostics are suppressed with `suppress=True`.

::: sprigconfig.deep_merge

## `ConfigSingleton`

`ConfigSingleton` stores one process-wide `Config` instance. Initialization is
explicit and may occur only once:

```python
from sprigconfig import ConfigSingleton

ConfigSingleton.initialize(profile="prod", config_dir="config")


def database_host():
    return ConfigSingleton.get()["database.host"]
```

`get()` before initialization and a second `initialize()` call raise
`ConfigLoadError`. Initialization and test cleanup use a lock; reads return the
already-created immutable-ish `Config` object.

The only reset API is the private `_clear_all()` test helper:

```python
import pytest
from sprigconfig import ConfigSingleton


@pytest.fixture(autouse=True)
def reset_config_singleton():
    ConfigSingleton._clear_all()
    yield
    ConfigSingleton._clear_all()
```

There is currently no public reload, clear, lazy-load, or `is_loaded` method.
Use direct `load_config()` calls when an application needs multiple independent
configurations.

::: sprigconfig.ConfigSingleton
    options:
      members:
        - initialize
        - get
