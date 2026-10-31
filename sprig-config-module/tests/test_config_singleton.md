# `test_config_singleton.py` — Singleton Regression Tests

## Intent

Check selected `ConfigSingleton` lifecycle and access behavior with the shared
test configuration fixture.

## Setup and assertions

An autouse fixture calls `_clear_all()` before and after each test. The tests
assert that:

- Initialization returns a `Config` and `get()` returns that same instance.
- A second initialization raises `ConfigLoadError`, including when the supplied
  profile or directory differs.
- Two concurrent initialization attempts produce one success and one
  `ConfigLoadError`.
- The test helper `reload_for_testing()` replaces the instance.
- Dotted-key access works and `load_config()` returns a separate instance.
- `_clear_all()` makes `get()` fail again.

## Evidence limits

The concurrency test exercises two threads in one constructed race; it does not
cover every scheduling or application lifecycle. Secret preservation through
the singleton is covered by the dedicated security tests.

## Run

From `sprig-config-module/`:

```bash
poetry run pytest tests/test_config_singleton.py
```
