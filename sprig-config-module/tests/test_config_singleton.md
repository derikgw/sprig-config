# Documentation for `tests/test_config_singleton.py`

This document explains the purpose, structure, and behavioral guarantees defined by the tests in:

```
tests/test_config_singleton.py
```

This test suite defines the **contract** for SprigConfig’s `ConfigSingleton` — a Java-style singleton designed for controlled, one-time initialization of configuration for application runtimes.

The file corresponds to the Markdown documentation:

```
tests/test_config_singleton.md
```

---

# 🎯 Purpose of `ConfigSingleton`

The `ConfigSingleton` is intended for environments where:

- Only **one** configuration should ever exist per process.
- Initialization must be **explicit**, **deterministic**, and **thread‑safe**.
- Runtime config lookups via `ConfigSingleton.get()` must never surprise the user.
- The singleton must **not** depend on nor interfere with `load_config()`.

The tests in this file establish the required rules for correct singleton behavior.

---

# 🧹 1. Test Fixture: Automatic Clearing

```python
@pytest.fixture(autouse=True)
def clear_singleton():
```

Before and after every test:

- `_clear_all()` is called.
- Ensures isolation between tests.
- Prevents stale state from leaking across the suite.

This mirrors how singletons are normally reset only in testing contexts, never in production.

---

# 📂 2. Basic Singleton Behavior

## `test_singleton_returns_config_instance`

Ensures:
- `initialize()` returns a valid `Config`.
- `get()` returns the same object.

This establishes the most fundamental singleton guarantee.

---

## `test_singleton_same_instance_for_same_profile_and_dir`

Verifies:
- Repeated calls to `get()` always return the same instance.

Reinforces immutability of initialization.

---

## `test_singleton_initialize_cannot_be_called_twice`

Ensures:
- A second call to `initialize()` raises `ConfigLoadError`.

This enforces the **"initialize once"** contract.

---

## `test_singleton_cannot_initialize_with_different_profile`
## `test_singleton_cannot_initialize_with_different_config_dir`

Ensures:
- The singleton cannot be reinitialized with different settings.
- Prevents accidental configuration drift.

These errors protect application runtime correctness.

---

# 🔒 3. Thread‑Safety

## `test_singleton_thread_safety`

Two threads race to initialize the singleton.

Expectations:
- Exactly **one** thread succeeds.
- The other raises `ConfigLoadError`.
- `get()` returns the successful instance.

This enforces **atomicity** and protects multi-threaded servers (e.g., WSGI or async worker pools).

---

# 🔄 4. Test‑Only Reload Support

The tests define:

## `test_singleton_reload_replaces_instance`
## `test_reload_only_affects_after_reload`

`reload_for_testing()` must:

- Replace the singleton with a fresh instance.
- Return the new instance.
- Update `get()` to reflect the new value.

Why?
- Allows reinitialization during tests without violating production guarantees.
- Simplifies integration tests that need fresh config states.

---

# 🧭 5. Dotted-Key Access Through Singleton

## `test_singleton_provides_dotted_key_access`

Ensures:
- The object returned by the singleton supports `.get("a.b.c")`.

This requires `ConfigSingleton` to return a `Config` object, not raw dicts.

---

# 🔑 6. Secret Handling Through Singleton

## `test_singleton_preserves_lazysecret_objects`

Ensures:
- Secrets remain as `LazySecret` or compatible objects.
- Singleton does not modify, unwrap, or leak secrets.

This is important for security consistency.

---

# 🔧 7. Backward Compatibility

## `test_load_config_independent_of_singleton`

Ensures:
- The singleton **does not affect** or depend upon `load_config()`.
- Both return independent `Config` objects.
- Loaders remain usable outside of singleton use cases.

This preserves compatibility with earlier versions of SprigConfig.

---

# 🧹 8. Clearing Behavior

## `test_singleton_clear_all_resets_state`

Ensures:
- `_clear_all()` wipes all internal state.
- After clearing, calling `get()` raises `ConfigLoadError`.

This solidifies expected reset behavior for test environments.

---

# ✔️ Summary

This test suite defines a **strict, predictable, Java-style singleton model** for SprigConfig:

| Feature | Required Behavior |
|--------|-------------------|
| Initialize once | ✔️ |
| Thread-safe | ✔️ |
| Cannot reinitialize with different profile | ✔️ |
| Cannot reinitialize with different config_dir | ✔️ |
| Access via `get()` | ✔️ |
| Separate from `load_config()` | ✔️ |
| Supports reload for tests | ✔️ |
| Supports dotted-key and secret handling | ✔️ |
| Full state reset via `_clear_all()` | ✔️ |

These guarantees ensure that SprigConfig behaves safely and predictably in production environments while remaining test‑friendly and backward compatible.

---

If you'd like, I can now generate:

- A developer-facing design doc for implementing a correct singleton.
- UML diagrams for the lifecycle.
- API docs for all public methods in `ConfigSingleton`.

