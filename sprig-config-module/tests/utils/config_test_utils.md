# config_test_utils.md

## Test Utility: `reload_for_testing`

This module provides a **test-only helper** for resetting and reinitializing
the SprigConfig singleton. It replaces the former
`ConfigSingleton.reload_for_testing()` method, which has been removed from
runtime code to keep the production API clean.

---

## Purpose

SprigConfig’s production architecture treats `ConfigSingleton` as:

- Initialized **exactly once**.
- Immutable and globally shared.
- Thread-safe.
- Illegal to reinitialize.

This is correct for real applications, but it creates challenges in tests:

- Tests need an isolated config state.
- Tests may load different profiles repeatedly.
- Tests must avoid cross-test contamination.
- Tests must never rely on long-lived global state.

The helper in `tests/utils/config_test_utils.py` solves this.

---

## API

### `reload_for_testing(*, profile: str, config_dir: Path) -> Config`

```python
from sprigconfig.config_singleton import ConfigSingleton
from pathlib import Path

def reload_for_testing(*, profile: str, config_dir: Path):
    """
    Test-only helper: fully resets and reloads ConfigSingleton.
    """
    ConfigSingleton._clear_all()
    return ConfigSingleton.initialize(profile=profile, config_dir=config_dir)
```

### Behavior

- Calls `_clear_all()` to wipe **all** singleton state.
- Immediately reinitializes using the given profile and directory.
- Guarantees reproducible and isolated config loads between tests.
- Is safe only in a **pytest environment** — never in production.

---

## Why This Was Moved Out of Runtime Code

Previously, `ConfigSingleton` exposed a `reload_for_testing()` classmethod.
Including test hooks in production API surfaces leads to:

- Accidental misuse in real apps.
- Violations of the “initialize exactly once” rule.
- Confusing semantics and additional maintenance burden.

Moving this into a **test utility** provides:

- A smaller, safer production API.
- Cleaner test design.
- Zero risk that production code reinitializes configuration.

---

## Which Markdown File Should Be Updated?

The file that must be modified is:

### **`config_singleton.md`**

This file previously documented `reload_for_testing()` as part of the runtime API.
You should update that documentation to:

- Remove all references to `reload_for_testing()`.
- Add a note that test-only reset helpers now live in `tests/utils/config_test_utils.py`.
- Clearly state that `ConfigSingleton` CAN NOT be reinitialized in production code.

