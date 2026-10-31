# `tests/conftest.py` — Shared Test Setup

`conftest.py` defines shared configuration-directory fixtures, environment
loading, optional config dumps, test logging, and conditional skipping for tests
marked `crypto`.

## Configuration fixtures

- `patch_config_dir` returns the repository's `tests/config` path.
- `use_real_config_dir` sets `APP_CONFIG_DIR` from the project `.env` value
  when present, otherwise uses `tests/config`.
- `full_config_dir` makes a temporary copy of `tests/config`; tests can mutate
  that copy without changing the repository fixtures.
- `base_config_dir` is a deprecated fixture that builds a minimal temporary
  YAML config.
- `load_test_config` and `load_raw_config` are legacy convenience wrappers.

The session `load_env` fixture loads the path selected by `--env-path`, or the
project-root `.env` when present. It supplies `tests/config` as the default
`APP_CONFIG_DIR` if the variable is unset. `resolved_env_path` rejects missing,
directory, or unreadable override paths.

## Diagnostics and secret handling

The pytest options are:

| Option | Behavior |
|---|---|
| `--env-path <file>` | Load the selected environment file |
| `--dump-config` | Print merged config through `maybe_dump` |
| `--dump-config-format yaml\|json` | Select the print format |
| `--dump-config-secrets` | Resolve `LazySecret` values for the dump |
| `--dump-config-no-redact` | Do not redact resolved secret values |
| `--debug-dump <file>` | Write captured config in redacted YAML form |
| `RUN_CRYPTO=true` | Enable tests marked `crypto`; otherwise they are skipped |

`_to_plain()` and `dump_config()` preserve `LazySecret` placeholders by default.
Combining secret resolution with `--dump-config-no-redact` can print plaintext
secrets. Do not use that mode with real credentials or share its output.
`capture_config` writes a dump only when `--debug-dump` is provided and a config
was captured.

## Logging

The session fixture writes timestamped logs under `test_logs/` and also adds a
console handler. CLI tests that need isolated subprocess output manage logging
separately.

## Evidence limits

These are shared conveniences, not a guarantee that every test is isolated or
that every debug-output path is secret-safe. Individual tests may use
environment monkeypatching, temporary directories, direct internal imports, or
explicit secret-revealing options. Review each test's setup and assertions when
assessing what it establishes.

## Run

From `sprig-config-module/`:

```bash
poetry run pytest
poetry run pytest --env-path=/path/to/test.env
poetry run pytest --debug-dump=/tmp/config.yml
```
