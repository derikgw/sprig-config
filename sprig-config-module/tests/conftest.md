
# Documentation for `tests/conftest.py`

This document describes the purpose, structure, and behavior of
`tests/conftest.py` inside the SprigConfig test suite.

It defines:

- Global pytest fixtures  
- CLI flags (“adoption flags”)  
- Test-time config directory overrides  
- Logging controls  
- Safe serialization helpers  
- Debug-dump tooling  
- Conditional test skipping  

This file ensures every test runs in a predictable, controlled, and fully 
debuggable environment.

---

# 📌 Overview

`conftest.py` provides the core testing infrastructure for SprigConfig:

- Environment-driven config loading  
- Support for `.env`–based configuration  
- Reusable config-directory fixtures  
- Backward compatibility loaders  
- Debug-friendly logging  
- Dumping merged configs to stdout or files  
- Skipping crypto tests unless explicitly enabled  
- Support for dynamic `.env` selection via `--env-path`

These tools make it possible to test SprigConfig under a wide variety of 
scenarios without modifying real application files.

---

# 🧱 1. Public API Enforcement

The test suite imports future public SprigConfig API symbols at the top level:

```python
from sprigconfig import (
    load_config,
    ConfigLoader,
    Config,
    ConfigSingleton,
    ConfigLoadError,
)
```

**Why?**

- Enforces TDD: if the future architecture changes, tests fail immediately.
- Prevents tests from depending on private internal modules.
- Ensures API stability before release.

`LazySecret` is imported separately for secret-handling tests.

---

# 📂 2. Configuration Directory Fixtures

These fixtures control how tests discover and load YAML configuration.

## `patch_config_dir`
Returns:

```
tests/config/
```

Used when tests need a stable, immutable config directory.

---

## `use_real_config_dir`
Simulates production behavior by setting:

```
APP_CONFIG_DIR
```

– using priority order:

1. `--env-path` (new)
2. `.env` inside the real project root  
3. default fallback → `tests/config`

**Why this matters:**  
SprigConfig relies heavily on environment-supplied config; tests must replicate 
that mechanism faithfully.

---

## `full_config_dir`
Creates a temporary **copy** of `tests/config`, retaining all recursive 
imports, overlays, and merge structures.

Used for tests that mutate config files or depend on complex directory layouts.

---

## `base_config_dir`
A deprecated minimal config directory generator.  
Retained only for legacy tests.

---

## `load_test_config` / `load_raw_config`
Compatibility wrappers around `load_config()`.  
New tests should use `ConfigLoader` directly.

---

# ⚙️ 3. Global Test Logging

Enables timestamped test logging in:

```
test_logs/pytest_<timestamp>.log
```

Also mirrors logs to stdout.

**Why?**

- Allows post-mortem debugging of failing tests  
- Captures deep-merge traces, import chains, and secret-resolution steps  
- Ensures consistency across engineers and CI environments

---

# 🚀 4. Adoption Flags (pytest CLI Options)

SprigConfig uses a series of pytest CLI flags to enable advanced debugging, 
controlled environment overrides, and optional behaviors.

This section explains every flag:

---

## **4.1 `--env-path`**  
**Purpose:**  
Override the `.env` file used during tests.

**What it does:**

- Allows tests to load variables (especially `APP_CONFIG_DIR`) from a custom `.env`
- Prevents modifying the real `.env`
- Enables CI pipelines or developers to inject controlled environment states

**Why it matters:**

- Ensures reproducible testing regardless of host environment  
- Allows simulation of “dev”, “staging”, “broken”, etc. environment files  
- Essential for testing import chains that depend on environment overlays

---

## **4.2 `--dump-config`**  
**Purpose:** Print the merged config for a test to stdout.

- Disabled by default  
- Useful in local debugging when you want to visually inspect merge results  

**Why:**  
Instant visibility into the final merged config without stepping through code.

---

## **4.3 `--dump-config-format yaml|json`**  
Sets the rendering format for `--dump-config`.

Defaults to YAML.

**Why:**  
Allows JSON diff tools or YAML-based test reviews depending on preference.

---

## **4.4 `--dump-config-secrets`**  
**Purpose:**  
Resolve `LazySecret` values before printing.

**But:** Values remain **redacted** unless `--dump-config-no-redact` is also used.

**Why:**  
Lets tests verify that secret resolution is functioning without revealing plaintext.

---

## **4.5 `--dump-config-no-redact`**  
**Purpose:**  
Print resolved secrets in plaintext.

**WARNING:**  
Not recommended outside isolated debugging sessions.

**Why:**  
Sometimes necessary for verifying correctness of encryption/decryption behavior.

---

## **4.6 `--debug-dump=/path/to/file.yml`**  
**Purpose:**  
Dump the **final merged config** for a test to a file after the test runs.

- Uses the `capture_config` fixture  
- Always writes in **safe, redacted** form  
- Allows deep inspection of merge behaviors, imports, overlays, and defaults  

**Why:**  

- Enables step-by-step debugging of failing merges  
- Works even when printing to stdout is noisy or disabled  
- Can be used in CI to archive merged configs for later review

---

## **4.7 `RUN_CRYPTO=true` (environment variable)**  
Not a CLI flag but part of the adoption API.

**Purpose:**  
Enable crypto-heavy tests.

If not set:

- Tests marked `@pytest.mark.crypto` are skipped automatically.

**Why:**  
Secret generation + Fernet operations can be slow.  
Most unit tests don’t need them.

---

# 🔒 5. Safe Serialization Helpers

`_to_plain()`  
Converts:

- `Config` → plain dict  
- `LazySecret` → placeholder or decrypted value  
- Nested lists, dicts, sets → serializable forms  

`dump_config()`  
Produces pretty YAML or JSON for display or debugging.

**Why:**  
Ensures consistent test output and prevents accidental secret exposure.

---

# 🐛 6. Legacy Fixture: `maybe_dump`

Supports:

```
--dump-config
--dump-config-format
--dump-config-secrets
--dump-config-no-redact
```

Used mostly for legacy debugging workflows.

---

# 🆕 7. `capture_config`: Debug Dump Fixture

Usage:

```python
cfg = capture_config(lambda: ConfigLoader(...).load())
```

If `--debug-dump` was passed:

- Writes final merged config to disk  
- Always redacted, safe, YAML-formatted  

**Why:**  
Great for debugging complicated config merges without manual print statements.

---

# 🧹 End of File

Intentionally ends with:

```
# =====================================================================
# END OF FILE
# =====================================================================
```

Indicating that no additional fixtures should be appended below.

---

# ✅ Summary Table

| Feature / Flag | Purpose |
|----------------|---------|
| `--env-path` | Choose custom `.env` for tests |
| `--dump-config` | Print merged config |
| `--dump-config-format` | YAML/JSON output |
| `--dump-config-secrets` | Resolve secrets |
| `--dump-config-no-redact` | Show plaintext secrets |
| `--debug-dump` | Write merged config to filesystem |
| `RUN_CRYPTO` | Enable crypto tests |
| Config fixtures | Control test config layout |
| Logging setup | Rich debug logs |
| `capture_config` | Snapshot merged config |
| `maybe_dump` | Legacy debug output |

SprigConfig’s test environment is designed to be:

- Deterministic  
- Debuggable  
- Safe  
- CI-friendly  
- Flexible to future architectural changes  

