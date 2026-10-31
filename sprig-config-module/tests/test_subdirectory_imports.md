# `test_subdirectory_imports.py` — In-Directory Import Behavior

## Intent

Check that a normal import from a subdirectory inside the configuration
directory remains usable.

## Scenarios and assertions

### `test_normal_subdirectory_imports_allowed`

Creates a temporary in-directory `imports/common.yml`, imports it, and asserts
that `server.port` is present in the loaded result. This checks that ordinary
subdirectory imports remain usable.

## Evidence limits

This functional test does not check path escape rejection or establish a
filesystem sandbox. Security checks for traversal and symlink escapes are
centralized under `security_tests/`.

## Run

From `sprig-config-module/`:

```bash
poetry run pytest tests/test_subdirectory_imports.py
```
