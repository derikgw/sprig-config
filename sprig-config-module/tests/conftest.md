# Documentation for `tests/conftest.py`

This document explains the purpose, structure, and behavior of the
`tests/conftest.py` file in the SprigConfig test suite.

The file defines **global pytest fixtures**, **CLI options**, **logging setup**,
and **serialization helpers** used across all system and integration tests.

It is named:

```
tests/conftest.md
```

to correspond to the Python file:

```
tests/conftest.py
```


---

# 📌 Overview

`conftest.py` establishes a standard testing environment for SprigConfig by:

- Setting up config directory fixtures  
- Providing compatibility loaders  
- Enabling detailed test logging  
- Adding pytest CLI options  
- Supporting safe config serialization  
- Supporting test-time debug dumps (`--debug-dump`)  
- Skipping crypto-heavy tests unless explicitly enabled  

This infrastructure ensures consistent behavior across all tests and supports
both **legacy** and **new** architecture paths.

---

# 🧱 1. Future Architecture Imports

SprigConfig is evolving toward a stable public API:

```python
from sprigconfig import (
    load_config,
    ConfigLoader,
    Config,
    ConfigSingleton,
    ConfigLoadError,
)
```

The file imports these symbols at the top-level to enforce that:

- Tests rely on the *public API*, not internal modules.
- If the API breaks, tests fail immediately (TDD-driven development).

`LazySecret` is imported separately for secret-handling tests.

---

# 📂 2. Configuration Directory Fixtures

These fixtures supply deterministic configuration directories for integration tests.

## `patch_config_dir`
A simple session-scoped fixture returning:

```
tests/config/
```

Used when tests only need a stable reference.

---

## `use_real_config_dir`
Sets:

```
APP_CONFIG_DIR = tests/config
```

This simulates real production usage where SprigConfig relies on the environment variable.

Most integration tests use this fixture.

---

## `full_config_dir`
Creates a **full temporary copy** of `tests/config`:

- Used for tests that mutate config files  
- Prevents accidental modification of real test configs  
- Enables multi-file merge behavior testing  

---

## `base_config_dir` (Deprecated)
Creates a **minimal** temporary config directory, writing only:

```yaml
logging:
  level: INFO
app:
  name: test-app
```

Kept only to support old tests.  
New tests should use `tests/config` + `use_real_config_dir`.

---

## `load_test_config`
Legacy helper that wraps `load_config()`:

```python
cfg = load_test_config(profile="dev")
```

Replaced by:

```python
cfg = ConfigLoader(config_dir, profile).load()
```

---

## `load_raw_config`
Thin wrapper around `load_config()`, used for negative tests.

---

# 🧾 3. Global Test Logging (session-wide)

The fixture:

```python
configure_test_logging
```

automatically:

- Creates `test_logs/` directory  
- Sets up a timestamped log file  
- Captures both console and file debug logs  
- Ensures clean handler initialization  

Logs look like:

```
2025-12-06 12:34:56 [INFO] tests.conftest: Test logging configured.
```

Useful for debugging complex merge or import problems.

---

# ⚙️ 4. Custom Pytest CLI Options

`pytest_addoption` adds several flags:

### **Debug printing:**
```
--dump-config
--dump-config-format yaml|json
--dump-config-secrets
--dump-config-no-redact
```

Used by the legacy `maybe_dump` fixture.

---

### **Write merged config to file:**
```
--debug-dump /path/to/file.yml
```

This instructs the new `capture_config` fixture to serialize the final config
after a test finishes.

Useful during development and debugging.

---

# 🚫 5. Conditional Test Skipping

`pytest_collection_modifyitems` enforces:

- Crypto tests run **only when**:

```
RUN_CRYPTO=true
```

This avoids unnecessary encryption/decryption overhead in normal test runs.

---

# 🔒 6. Safe Serialization Helpers

## `_to_plain(obj)`
Converts objects into safe, JSON/YAML-friendly structures.

Handles:

- `LazySecret` → placeholder or decrypted value
- `Config` → `dict`
- Nested dicts/lists/sets

Used by both dumps and debug logging.

---

## `dump_config(cfg, ...)`
Converts a final config to:

- Clean YAML  
- Pretty JSON  

While respecting:

- `resolve_secrets`  
- `redact`  

---

# 🐛 7. Legacy Fixture: `maybe_dump`

This fixture prints the merged config to stdout **only when**
`--dump-config` is provided.

It supports:

- YAML or JSON output  
- Secret resolution  
- Secret redaction flags  

Useful for debugging failing tests.

---

# 🆕 8. New Fixture: `capture_config`

Purpose:

> Capture the result of a config load and write it to a file if  
> `--debug-dump /path` is provided.

Usage:

```python
cfg = capture_config(lambda: ConfigLoader(...).load())
```

After the test finishes, if `--debug-dump` was passed:

- The merged config is serialized using `_to_plain`
- Written to a YAML file
- Secrets protected (redacted)

This is now the preferred tool for generating **post-merge debug snapshots**.

---

# 🧹 End of File

The file ends with:

```python
# =====================================================================
# END OF FILE
# =====================================================================
```

indicating no additional fixtures or helpers follow.

---

# ✅ Summary

`tests/conftest.py` provides the backbone of the SprigConfig test environment:

| Feature | Supported |
|--------|-----------|
| Public API imports | ✔️ |
| Config directory utilities | ✔️ |
| Legacy + modern loaders | ✔️ |
| Environment-driven config loading | ✔️ |
| Safe serialization | ✔️ |
| Debug dump tooling | ✔️ |
| Test logging | ✔️ |
| CLI options | ✔️ |
| Conditional skipping | ✔️ |

This file ensures every test runs in a predictable, controlled, debuggable environment while supporting both SprigConfig's legacy behavior and its emerging architecture.

