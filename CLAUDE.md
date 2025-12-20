# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **monorepo** containing two Python projects:

1. **sprig-config-module/** — Core SprigConfig runtime library (Spring Boot-style configuration for Python)
2. **sprig-tools/** — Developer utilities (not required to use SprigConfig)

Each project maintains its own isolated virtual environment managed by Poetry.

## Working with sprig-config-module (Primary Project)

The main development work occurs in `sprig-config-module/`. This is a Python 3.13+ library providing:
- Layered YAML configuration with deep merge semantics
- Runtime-driven profile selection (dev, test, prod)
- Recursive imports and provenance tracking
- Secure lazy secret handling with encryption
- Environment variable expansion

### Development Commands

All commands below assume you're in the `sprig-config-module/` directory:

```bash
# Install dependencies
poetry install

# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src --cov-report=xml

# Run specific test
poetry run pytest tests/test_config_loader.py

# Run single test function
poetry run pytest tests/test_config_loader.py::test_function_name

# Run tests excluding integration tests
poetry run pytest -m "not integration"

# Run tests excluding crypto tests
poetry run pytest -m "not crypto"

# Lint with ruff
poetry run ruff check src

# Run with custom .env file (tests)
poetry run pytest --env-path=/path/to/.env

# Debug merged config
poetry run pytest --dump-config --dump-config-format=yaml

# Enable crypto tests (requires APP_SECRET_KEY)
RUN_CRYPTO=true poetry run pytest
```

### Test Architecture

SprigConfig has a comprehensive test suite with documentation:
- Each test module (`test_*.py`) has a paired `.md` file explaining its purpose
- `tests/conftest.py` provides shared fixtures and test infrastructure
- `tests/conftest.md` documents the test framework architecture
- Test categories: config mechanics, metadata, deep merge, profile overlay, LazySecret, CLI, integration

Custom pytest flags available:
- `--env-path` — Use custom .env file during tests
- `--dump-config` — Print merged config for debugging
- `--dump-config-format yaml|json` — Output format
- `--dump-config-secrets` — Resolve LazySecrets
- `--dump-config-no-redact` — Show plaintext secrets
- `--debug-dump=file.yml` — Write merged config snapshot
- `RUN_CRYPTO=true` — Enable crypto-heavy tests

## Working with sprig-tools

Developer utilities in `sprig-tools/` include:
- `sprig-sync` — Keep pytest.ini and pyproject.toml in sync
- CLI tools for secret management

Commands (from `sprig-tools/` directory):

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run specific tool
poetry run sprig-tool
poetry run secret-cli
poetry run secret-quickdemo
```

## Architecture Notes

### Core Module Structure

Located in `sprig-config-module/src/sprigconfig/`:

- `config_loader.py` — Main configuration loading and merging logic
- `config.py` — Config class with dict-like interface and dotted-key access
- `lazy_secret.py` — LazySecret class for secure, deferred decryption of ENC(...) values
- `deepmerge.py` — Deep merge algorithm for layered YAML files
- `exceptions.py` — Custom exceptions (ConfigLoadError, etc.)
- `config_singleton.py` — Thread-safe cached loader
- `cli.py` — CLI interface for config inspection
- `help.py` — Help text and documentation

Each `.py` file has a paired `.md` file documenting its design.

### Configuration Loading Flow

1. **Profile resolution** (runtime-driven, never from files):
   - Explicit `load_config(profile=...)`
   - `APP_PROFILE` environment variable
   - pytest context → "test"
   - Default → "dev"

2. **File merging order**:
   - `application.yml` (base)
   - `application-<profile>.yml` (profile overlay)
   - Recursive `imports: [...]` from each file

3. **Processing**:
   - Deep merge with override collision warnings
   - Environment variable expansion (`${VAR}` or `${VAR:default}`)
   - ENC(...) values mapped to LazySecret objects
   - Metadata injection (`sprigconfig._meta`)

### Profile Behavior

- **CRITICAL**: Files should NOT contain `app.profile` — runtime determines this
- Profile is injected as `app.profile` in final config
- Production guardrails: missing `application-prod.yml` causes error, DEBUG logging blocked unless explicitly allowed

### Secret Management

- Secrets stored as `ENC(<ciphertext>)` in YAML
- Requires `APP_SECRET_KEY` environment variable (Fernet key)
- LazySecret objects decrypt on `.get()` call only
- Secrets are redacted in dumps unless explicitly requested
- Global key provider support available

## GitLab CI/CD

CI runs on GitLab (source of truth):

**Stages**: lint → test → security → deploy

- **lint**: `poetry run ruff check src`
- **pytest**: Full test suite with coverage reporting
- **security**: SAST and secret detection
- **deploy**: Manual PyPI publish for version tags (v*)

Version tags must match `pyproject.toml` version (case-insensitive, strips leading "v").

## Important Patterns

### Environment Variables

Configuration directory resolution:
1. `load_config(config_dir=...)` (explicit parameter)
2. `APP_CONFIG_DIR` environment variable
3. `.env` file in project root
4. Default: `./config`

Key environment variables:
- `APP_CONFIG_DIR` — Config directory path
- `APP_PROFILE` — Active profile (dev/test/prod)
- `APP_SECRET_KEY` — Fernet key for secret decryption

### .env Loading

`.env` files are loaded for local development. SprigConfig supports:
- Project root `.env` for default values
- Custom `.env` via `--env-path` flag in tests
- Direct environment variable overrides

### Git Workflow Notes

- Test config files may use `git update-index --skip-worktree` (see docs/git_skip_worktree_for_test_config_files.md)
- Use `git ls-files -v | grep ^S` to check skip-worktree status
- Changes to versioned test configs need explicit `git update-index --no-skip-worktree`

## Documentation Locations

- `sprig-config-module/README.md` — User-facing documentation
- `sprig-config-module/CONTRIBUTING.md` — Contribution guidelines for core module
- `sprig-config-module/docs/` — Developer guides, release checklists, design notes
- `sprig-config-module/ROADMAP.md` — Future plans
- `sprig-config-module/CHANGELOG.md` — Version history
- `CONTRIBUTING.md` (root) — General contribution overview

## Design Principles

From `sprig-config-module/CONTRIBUTING.md`:

- **Layered YAML** with deep merge semantics
- **Runtime-driven profile selection** (never from config files)
- **Deterministic, debuggable** configuration behavior
- **Backward compatibility** is critical for core behavior
- **Provenance tracking** for all config sources
- **Secure by default** for secrets

## Versioning

SprigConfig follows Semantic Versioning:
- **MAJOR**: Breaking changes
- **MINOR**: Backward-compatible functionality
- **PATCH**: Backward-compatible bug fixes

Pre-release versions (e.g., `-rc1`) are release candidates not recommended for production.

## Python Version Support

- **sprig-config-module**: Python 3.13+ (strict requirement)
- **sprig-tools**: Python 3.12-3.13

## Key Dependencies

**sprig-config-module**:
- PyYAML ≥6.0.2
- cryptography ^46.0.1
- python-dotenv (dev)

**sprig-tools**:
- tomli ≥2.2.1
- tomli-w ≥1.2.0 (import as `tomli_w`)
- cryptography ^46.0.1

## UTF-8 BOM Handling

YAML files are read using `utf-8-sig` encoding, which automatically strips UTF-8 BOM markers that can cause parser issues when files are created on Windows. This prevents keys like `ï»¿server` from appearing in parsed config.
