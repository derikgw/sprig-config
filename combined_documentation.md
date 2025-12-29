# File: CLAUDE.md

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



---

# File: CONTRIBUTING.md

# Contributing to SprigConfig

Thanks for your interest in contributing to **SprigConfig**.

This repository contains multiple components. Please read the section below to ensure your contribution lands in the right place.

---

## Repository Structure

- `sprig-config-module/`  
  Core SprigConfig implementation, including config loading, merging, and parsing logic.

- `sprig-tools/`  
  Supporting tools, utilities, or experimental helpers.

- `docs/` (if/when present)  
  Documentation and guides.

---

## Where to Contribute

### Core behavior, loaders, parsers, merge semantics

➡ See **sprig-config-module/CONTRIBUTING.md**

That document defines:
- architectural principles
- backward compatibility expectations
- supported formats and design constraints

### Tooling, CI, packaging, or docs

Contributions here should:
- be narrowly scoped
- include clear rationale
- avoid altering core behavior indirectly

---

## Issues and Pull Requests

- Please open an issue before large changes.
- Bug reports should include reproduction steps.
- Pull requests should include tests when applicable.

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.



---

# File: README.md

# 🌱 SprigConfig Monorepo

This repository is a **monorepo** containing the core SprigConfig runtime
along with supporting tools and developer utilities.

If you are looking to *use* SprigConfig in your Python project, you almost
certainly want **`sprig-config-module`**.

---

## 📦 sprig-config-module (Primary Project)
[![Latest Version](https://gitlab.com/dgw_software/sprig-config/-/badges/release.svg)](https://gitlab.com/dgw_software/sprig-config/-/packages)

The **core SprigConfig runtime** providing Spring Boot–style configuration
loading for Python applications.

This is the **authoritative package** published to PyPI and intended for
production use.

**Highlights**
- Layered YAML configuration with deep merge semantics
- Runtime-driven profile selection
- Recursive imports and provenance tracking
- Secure lazy secret handling
- Deterministic, debuggable configuration behavior

**Details**
- Language: Python 3.9+
- Primary dependency: PyYAML
- Location: `sprig-config-module/`

➡️ **Start here (authoritative docs):** [sprig-config-module/README.md](sprig-config-module/README.md)

---

## 🧰 sprig-tools (Supporting Utilities)

A collection of **developer-facing helper tools** used to support SprigConfig
development and related Python projects.

These tools are **not required** to use SprigConfig itself.

**Includes**
- `sprig-sync` — utilities for keeping `pytest.ini` and `pyproject.toml` in sync
- Miscellaneous development helpers

**Details**
- Language: Python 3.9+
- Dependencies: tomli / tomli_w
- Location: `sprig-tools/`

---

## 📘 Repository Notes

- GitLab is the **source of truth** for this repository
- GitHub mirrors may include the full monorepo
- Documentation for SprigConfig lives primarily under:
  - `sprig-config-module/`
  - `sprig-config-module/docs/`
- **Authoritative CHANGELOG:** `sprig-config-module/CHANGELOG.md`

---

## 📄 License

MIT



---

# File: SETUP.md

# SprigConfig Mono-Repo Setup

This repository contains two subprojects:

- **sprig-config-module** – Main runtime library
- **sprig-tools** – Developer helper utilities

Each project maintains its own isolated virtual environment and can be opened in an IDE
with convenience scripts.

---

## Launching IDEs

### `open-module.sh`
Launches the `sprig-config-module` project in VS Code (default) or PyCharm.

```bash
./open-module.sh           # Opens VS Code in sprig-config-module
./open-module.sh pycharm   # Opens PyCharm in sprig-config-module
```

- **VS Code** will open `sprig-config-module.code-workspace` (if present).
- **PyCharm** will open the project folder and use `.venv` interpreter.

---

### `open-tools.sh`
Launches the `sprig-tools` project in VS Code (default) or PyCharm.

```bash
./open-tools.sh            # Opens VS Code in sprig-tools
./open-tools.sh pycharm    # Opens PyCharm in sprig-tools
```

- **VS Code** will open `sprig-tools.code-workspace` (if present).
- **PyCharm** will open the project folder and use `.venv` interpreter.

---

## Recommended IDE Settings

### VS Code
- Use `Python: Select Interpreter` to set interpreter to `${workspaceFolder}/.venv`.
- Save a `.code-workspace` in each project folder for extra folders/settings.

### PyCharm
- `Settings > Project > Python Interpreter` → set interpreter to project `.venv`.
- Change `File > Settings > Project Opening` to `New Window` for multi-window workflows.

---

## Why Workspaces and `.idea` Are Not Versioned
- IDE config files (`.code-workspace`, `.idea`) are **not committed** to keep repo clean.
- Setup instructions ensure any developer can recreate these with minimal steps.

---

## Creating VS Code Workspaces

### sprig-config-module
1. Open VS Code in `sprig-config-module`.
2. `File > Add Folder to Workspace` if you want more folders.
3. `File > Save Workspace As...` → save as `sprig-config-module.code-workspace` in project folder.

### sprig-tools
1. Open VS Code in `sprig-tools`.
2. `File > Add Folder to Workspace` if you want more folders.
3. `File > Save Workspace As...` → save as `sprig-tools.code-workspace` in project folder.



---

# File: docs/api/core.md

# Core API

The core API provides the primary interfaces for loading and accessing configuration.

## load_config()

The main entry point for loading configuration. This is a convenience function that creates a `ConfigLoader` instance and returns a `Config` object.

::: sprigconfig.load_config

**Example:**

```python
from sprigconfig import load_config

# Basic usage
cfg = load_config()

# With explicit profile
cfg = load_config(profile="prod")

# With custom config directory
cfg = load_config(config_dir="/etc/myapp/config")
```

---

## Config

A dict-like wrapper that provides convenient access to configuration values with support for dotted-key notation.

::: sprigconfig.Config
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - get
        - __getitem__
        - __setitem__
        - __contains__
        - keys
        - values
        - items
        - to_dict

**Example:**

```python
from sprigconfig import load_config

cfg = load_config()

# Dict-like access
db_host = cfg["database"]["host"]

# Dotted-key access
db_host = cfg.get("database.host")

# Default values
timeout = cfg.get("database.timeout", 30)

# Check if key exists
if "features.analytics" in cfg:
    print("Analytics configured")

# Iterate over keys
for key in cfg.keys():
    print(key)

# Convert to plain dict
plain_dict = cfg.to_dict()
```

---

## ConfigLoader

The primary configuration loading engine. Handles file discovery, parsing, merging, profile overlays, and imports.

::: sprigconfig.ConfigLoader
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - load
        - _resolve_profile
        - _resolve_config_dir

**Example:**

```python
from sprigconfig import ConfigLoader
from pathlib import Path

# Create loader with explicit settings
loader = ConfigLoader(
    config_dir=Path("./config"),
    profile="prod"
)

# Load configuration
cfg = loader.load()

# Access values
print(cfg.get("app.name"))
```

**Advanced Usage:**

```python
# Programmatic profile resolution
import os

profile = os.environ.get("DEPLOY_ENV", "dev")
loader = ConfigLoader(profile=profile)
cfg = loader.load()

# Custom config directory from environment
config_dir = os.environ.get("APP_CONFIG_DIR", "./config")
loader = ConfigLoader(config_dir=config_dir)
cfg = loader.load()
```

---

## Key Concepts

### Configuration Loading Flow

1. **Profile Resolution**: Determine active profile (explicit, `APP_PROFILE`, pytest context, or 'dev')
2. **Directory Resolution**: Locate config directory (explicit, `APP_CONFIG_DIR`, or './config')
3. **File Discovery**: Find `application.<ext>` and `application-<profile>.<ext>`
4. **Parsing**: Parse configuration files (YAML, JSON, or TOML)
5. **Merging**: Deep merge base + imports + profile + profile imports
6. **Processing**: Expand environment variables, create LazySecret objects
7. **Metadata**: Inject `sprigconfig._meta` with provenance information

### Profile Behavior

Profiles are **runtime-driven** and never read from configuration files:

- Explicit: `load_config(profile="prod")`
- Environment: `APP_PROFILE=prod`
- Pytest: Automatically uses "test"
- Default: "dev"

### File Formats

SprigConfig supports three configuration formats:

- **YAML** (`.yml`, `.yaml`) - Default, most common
- **JSON** (`.json`) - Structured data
- **TOML** (`.toml`) - Configuration-focused

**Important:** Use exactly one format per project. Mixed-format imports are not supported.

### Merge Semantics

Configuration is merged in this order (later overrides earlier):

1. `application.<ext>` (base)
2. Base imports
3. `application-<profile>.<ext>` (profile overlay)
4. Profile imports

This ensures profile-specific settings always have final say.

---

## Thread Safety

All core API components are thread-safe:

- `load_config()` can be called from multiple threads
- `Config` objects are safe for concurrent reads
- Use `ConfigSingleton` for shared configuration across threads

See [Utilities API](utilities.md#configsingleton) for thread-safe caching patterns.



---

# File: docs/api/exceptions.md

# Exceptions API

Error handling and exception classes for SprigConfig.

## ConfigLoadError

Base exception for all configuration loading errors.

::: sprigconfig.exceptions.ConfigLoadError
    options:
      show_root_heading: true
      show_source: true

**Example:**

```python
from sprigconfig import load_config, ConfigLoadError

try:
    cfg = load_config(profile="prod")
except ConfigLoadError as e:
    print(f"Failed to load configuration: {e}")
    # Handle error (use defaults, exit, etc.)
```

---

## Exception Hierarchy

SprigConfig uses a simple exception hierarchy:

```
Exception
└── ConfigLoadError (base for all config errors)
```

All configuration-related errors inherit from `ConfigLoadError`, making it easy to catch any config-related issue:

```python
try:
    cfg = load_config()
except ConfigLoadError:
    # Catches all config-related errors
    handle_config_error()
```

---

## Common Error Scenarios

### 1. Missing Configuration File

**Scenario:** Required configuration file not found

```python
# config/application.yml does not exist
from sprigconfig import load_config, ConfigLoadError

try:
    cfg = load_config()
except ConfigLoadError as e:
    print(f"Error: {e}")
    # "Configuration file not found: config/application.yml"
```

**Solutions:**
- Create the missing file
- Check `config_dir` parameter
- Set `APP_CONFIG_DIR` environment variable

### 2. Production Profile Missing

**Scenario:** Production mode requires `application-prod.yml` to exist

```python
from sprigconfig import load_config, ConfigLoadError

try:
    cfg = load_config(profile="prod")
except ConfigLoadError as e:
    print(f"Error: {e}")
    # "Production profile requires application-prod.yml"
```

**Solution:**
- Create `config/application-prod.yml`
- This is a safety feature to prevent accidental production deployments with dev config

### 3. Invalid YAML/JSON/TOML Syntax

**Scenario:** Configuration file has syntax errors

```yaml
# config/application.yml (invalid)
database:
  host: localhost
  port: [invalid syntax here
```

```python
from sprigconfig import load_config, ConfigLoadError

try:
    cfg = load_config()
except ConfigLoadError as e:
    print(f"Parse error: {e}")
```

**Solutions:**
- Validate YAML/JSON/TOML syntax
- Use a linter or validator
- Check for common issues (indentation, quotes, commas)

### 4. Circular Import Detected

**Scenario:** Configuration files import each other in a loop

```yaml
# config/application.yml
imports:
  - database.yml

# config/database.yml
imports:
  - application.yml  # Circular!
```

```python
from sprigconfig import load_config, ConfigLoadError

try:
    cfg = load_config()
except ConfigLoadError as e:
    print(f"Error: {e}")
    # "Circular import detected: application.yml -> database.yml -> application.yml"
```

**Solution:**
- Remove circular imports
- Restructure your configuration files
- Use a hierarchical import structure

### 5. Missing Encryption Key

**Scenario:** Configuration has encrypted secrets but `APP_SECRET_KEY` not set

```yaml
# config/application.yml
database:
  password: ENC(gAAAAAB...)  # Encrypted secret
```

```python
from sprigconfig import load_config

cfg = load_config()

# Later, when trying to decrypt
try:
    password = cfg["database"]["password"].get()
except Exception as e:
    print(f"Decryption error: {e}")
    # "No encryption key available"
```

**Solutions:**
- Set `APP_SECRET_KEY` environment variable
- Use `LazySecret.set_global_key_provider()`
- Pass key explicitly: `secret.get(key="your-key")`

### 6. Invalid Configuration Directory

**Scenario:** Specified config directory doesn't exist

```python
from sprigconfig import load_config, ConfigLoadError

try:
    cfg = load_config(config_dir="/nonexistent/path")
except ConfigLoadError as e:
    print(f"Error: {e}")
    # "Configuration directory not found: /nonexistent/path"
```

**Solution:**
- Verify the path exists
- Check file permissions
- Use absolute paths to avoid ambiguity

---

## Error Handling Patterns

### Pattern 1: Graceful Degradation

```python
from sprigconfig import load_config, ConfigLoadError

def get_config():
    """Load config with fallback to defaults."""
    try:
        return load_config()
    except ConfigLoadError as e:
        print(f"Warning: Using default config due to: {e}")
        return {
            "database": {"host": "localhost", "port": 5432},
            "app": {"debug": False}
        }

cfg = get_config()
```

### Pattern 2: Fail Fast

```python
from sprigconfig import load_config, ConfigLoadError
import sys

try:
    cfg = load_config(profile="prod")
except ConfigLoadError as e:
    print(f"FATAL: Cannot load configuration: {e}", file=sys.stderr)
    sys.exit(1)

# Continue with valid config
```

### Pattern 3: Detailed Error Logging

```python
import logging
from sprigconfig import load_config, ConfigLoadError

logger = logging.getLogger(__name__)

try:
    cfg = load_config()
except ConfigLoadError as e:
    logger.error(
        "Configuration load failed",
        exc_info=True,
        extra={
            "error": str(e),
            "profile": "dev",
            "config_dir": "./config"
        }
    )
    raise
```

### Pattern 4: Retry with Fallback

```python
from sprigconfig import load_config, ConfigLoadError
import os

def load_with_fallback():
    """Try loading from primary location, then fallback."""
    try:
        return load_config(config_dir="/etc/myapp/config")
    except ConfigLoadError:
        # Try fallback location
        try:
            return load_config(config_dir="./config")
        except ConfigLoadError as e:
            raise ConfigLoadError(
                f"Failed to load config from primary and fallback locations: {e}"
            )

cfg = load_with_fallback()
```

---

## Validation and Error Prevention

### Pre-flight Checks

```python
from pathlib import Path
from sprigconfig import load_config, ConfigLoadError

def validate_config_setup(profile="dev"):
    """Validate configuration before loading."""
    config_dir = Path("./config")

    # Check directory exists
    if not config_dir.exists():
        raise ConfigLoadError(f"Config directory not found: {config_dir}")

    # Check base file exists
    base_file = config_dir / "application.yml"
    if not base_file.exists():
        raise ConfigLoadError(f"Base config not found: {base_file}")

    # Check profile file exists (for prod)
    if profile == "prod":
        profile_file = config_dir / f"application-{profile}.yml"
        if not profile_file.exists():
            raise ConfigLoadError(f"Profile config not found: {profile_file}")

    return True

# Validate before loading
validate_config_setup(profile="prod")
cfg = load_config(profile="prod")
```

### Custom Validation

```python
from sprigconfig import load_config, ConfigLoadError

def load_and_validate():
    """Load config and validate required keys."""
    cfg = load_config()

    # Validate required keys
    required_keys = [
        "database.host",
        "database.port",
        "app.name"
    ]

    for key in required_keys:
        if key not in cfg:
            raise ConfigLoadError(f"Required configuration key missing: {key}")

    # Validate value types
    if not isinstance(cfg.get("database.port"), int):
        raise ConfigLoadError("database.port must be an integer")

    return cfg

cfg = load_and_validate()
```

---

## Debugging Configuration Errors

### Enable Debug Logging

```python
import logging
from sprigconfig import load_config

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Load config (will show detailed debug info)
cfg = load_config()
```

### Use CLI for Inspection

```bash
# Dump configuration to see what's loaded
sprigconfig dump --profile dev

# Validate configuration syntax
sprigconfig dump --profile prod --format yaml
```

### Check Configuration Files

```python
import yaml
from pathlib import Path

# Manually validate YAML syntax
config_file = Path("config/application.yml")
try:
    with open(config_file) as f:
        data = yaml.safe_load(f)
    print(f"Valid YAML: {config_file}")
except yaml.YAMLError as e:
    print(f"Invalid YAML: {e}")
```

---

## Error Messages

SprigConfig provides clear, actionable error messages:

| Error | Message | Solution |
|-------|---------|----------|
| Missing file | `Configuration file not found: config/application.yml` | Create the file or check path |
| Parse error | `Failed to parse config/application.yml: invalid syntax` | Fix YAML/JSON/TOML syntax |
| Circular import | `Circular import detected: a.yml -> b.yml -> a.yml` | Remove circular dependency |
| Production guard | `Production profile requires application-prod.yml` | Create prod config file |
| Missing key | `Required key not found: database.host` | Add missing configuration |

---

## Best Practices

1. **Always catch ConfigLoadError** - Don't let config errors crash silently
2. **Log detailed errors** - Include context (profile, paths) in error logs
3. **Validate early** - Check config at startup, not during requests
4. **Provide defaults** - Have sensible fallbacks for non-critical config
5. **Test error paths** - Write tests for config loading failures
6. **Document required config** - Make it clear what config is needed

---

## Related Documentation

- [Core API](core.md) - Main configuration loading
- [Configuration Guide](../configuration.md) - General usage patterns
- [FAQ](../faq.md) - Common questions and troubleshooting



---

# File: docs/api/index.md

# API Reference

Welcome to the SprigConfig API reference documentation. This section provides detailed information about all public classes, functions, and modules.

## Quick Links

- [Core API](core.md) - `load_config()`, `Config`, `ConfigLoader`
- [Secrets](secrets.md) - `LazySecret` for encrypted configuration
- [Utilities](utilities.md) - `deep_merge()`, `ConfigSingleton`
- [Exceptions](exceptions.md) - Error handling and custom exceptions

## Public API Overview

SprigConfig exposes a minimal, stable API surface designed for ease of use and backward compatibility.

### Essential Imports

```python
from sprigconfig import load_config, Config, ConfigLoader
from sprigconfig import ConfigLoadError
from sprigconfig.lazy_secret import LazySecret
```

### API Stability Guarantees

- **Public API** (documented here): Stable, follows semantic versioning
- **Internal modules** (not documented): May change without notice
- **Deprecations**: Announced one minor version in advance

## Common Patterns

### Basic Configuration Loading

```python
from sprigconfig import load_config

# Load with automatic profile detection
cfg = load_config()

# Load with explicit profile
cfg = load_config(profile="prod")

# Load from custom directory
cfg = load_config(config_dir="/path/to/config")
```

### Using ConfigLoader Directly

```python
from sprigconfig import ConfigLoader

loader = ConfigLoader(
    config_dir="./config",
    profile="dev"
)
cfg = loader.load()
```

### Accessing Configuration

```python
# Dict-like access
db_host = cfg["database"]["host"]

# Dotted-key access
db_host = cfg.get("database.host")

# With defaults
db_port = cfg.get("database.port", 5432)
```

### Working with Secrets

```python
from sprigconfig.lazy_secret import LazySecret

# Secrets are LazySecret objects until decrypted
db_password = cfg["database"]["password"]  # LazySecret
actual_password = db_password.get()  # Decrypted string
```

## Module Organization

SprigConfig's public API is intentionally minimal:

```
sprigconfig/
├── __init__.py           # Public API exports
├── config.py             # Config class (dict-like wrapper)
├── config_loader.py      # ConfigLoader (main loading logic)
├── config_singleton.py   # ConfigSingleton (global cache)
├── lazy_secret.py        # LazySecret (encrypted values)
├── deepmerge.py          # deep_merge utility
├── exceptions.py         # ConfigLoadError and subclasses
├── cli.py                # Command-line interface
└── parsers/              # Internal parsers (YAML, JSON, TOML)
```

**Note:** Only modules listed in `sprigconfig.__all__` are part of the public API.

## Type Hints

SprigConfig is fully type-annotated. Use type checkers like mypy:

```python
from sprigconfig import Config, load_config

cfg: Config = load_config(profile="dev")
```

## Next Steps

- Browse the [Core API](core.md) for main functionality
- Check [Secrets](secrets.md) for encrypted configuration
- See [Configuration Guide](../configuration.md) for usage patterns
- Review [Examples](https://gitlab.com/dgw_software/sprig-config/-/tree/main/sprig-config-module/examples) for real-world code



---

# File: docs/api/secrets.md

# Secrets API

SprigConfig provides secure secret management through the `LazySecret` class, which handles encrypted configuration values.

## LazySecret

A secure wrapper for encrypted configuration values that provides lazy decryption and automatic redaction.

::: sprigconfig.lazy_secret.LazySecret
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - get
        - encrypt
        - set_global_key_provider
        - __repr__
        - __str__

---

## Usage Patterns

### Basic Secret Usage

```python
from sprigconfig import load_config

cfg = load_config()

# Secret is still encrypted at this point
db_password = cfg["database"]["password"]  # LazySecret object

# Decrypt only when needed
actual_password = db_password.get()  # "my-secret-password"
```

### Encrypting Secrets

```python
from sprigconfig.lazy_secret import LazySecret
import os

# Get encryption key from environment
key = os.environ["APP_SECRET_KEY"]

# Encrypt a secret
encrypted = LazySecret.encrypt("my-secret-value", key)
print(encrypted)  # ENC(gAAAAAB...)

# Use in configuration file
# database:
#   password: ENC(gAAAAAB...)
```

### Global Key Provider

For advanced scenarios, set a global key provider instead of using environment variables:

```python
from sprigconfig.lazy_secret import LazySecret

def get_key_from_vault():
    # Fetch key from HashiCorp Vault, AWS Secrets Manager, etc.
    return fetch_from_vault("encryption-key")

# Set global key provider
LazySecret.set_global_key_provider(get_key_from_vault)

# Now all LazySecret.get() calls will use this key
cfg = load_config()
password = cfg["database"]["password"].get()  # Uses global provider
```

### Per-Secret Keys

For maximum security, use different keys for different secrets:

```python
from sprigconfig.lazy_secret import LazySecret

# Encrypt with specific key
db_key = "db-specific-encryption-key"
encrypted_db_pass = LazySecret.encrypt("db-password", db_key)

# Later, decrypt with the same key
db_password = cfg["database"]["password"]
actual_password = db_password.get(key=db_key)
```

---

## ENC() Format

Secrets in configuration files use the `ENC()` format:

```yaml
# config/application.yml
database:
  host: localhost
  username: admin
  password: ENC(gAAAAABm...)  # Encrypted with Fernet

api:
  key: ENC(gAAAAABn...)  # Another encrypted value
```

When SprigConfig loads this file:
1. Detects `ENC(...)` values
2. Creates `LazySecret` objects (not yet decrypted)
3. Decryption happens only when `.get()` is called

---

## Security Features

### Lazy Evaluation

Secrets are not decrypted until explicitly requested:

```python
# Load config - secrets remain encrypted
cfg = load_config()

# Access secret object - still encrypted
secret = cfg["api"]["key"]  # LazySecret object

# Decrypt only when needed
api_key = secret.get()  # Now decrypted
```

**Benefits:**
- Prevents accidental exposure in logs
- Reduces attack surface
- Secrets stay encrypted in memory until needed

### Automatic Redaction

LazySecret objects are automatically redacted in string representations:

```python
secret = cfg["database"]["password"]

print(secret)           # LazySecret(redacted)
print(repr(secret))     # LazySecret(redacted)
print(str(secret))      # LazySecret(redacted)

# Only .get() reveals the actual value
print(secret.get())     # my-secret-password
```

This prevents accidental exposure in:
- Log files
- Error messages
- Debug output
- Exception tracebacks

### Key Management

SprigConfig supports multiple key sources (in priority order):

1. **Explicit key parameter**: `secret.get(key="specific-key")`
2. **Global key provider**: `LazySecret.set_global_key_provider(provider_func)`
3. **Environment variable**: `APP_SECRET_KEY`

```python
import os
from sprigconfig.lazy_secret import LazySecret

# Method 1: Environment variable (simplest)
os.environ["APP_SECRET_KEY"] = "your-fernet-key"

# Method 2: Global provider (flexible)
def get_key():
    return fetch_from_secret_manager()

LazySecret.set_global_key_provider(get_key)

# Method 3: Explicit key (per-secret)
password = secret.get(key="specific-key-for-this-secret")
```

---

## Encryption Details

SprigConfig uses **Fernet** (symmetric encryption) from the `cryptography` library:

- **Algorithm**: AES-128-CBC with HMAC-SHA256
- **Key size**: 32 bytes (URL-safe base64-encoded)
- **Security**: Authenticated encryption (prevents tampering)

### Generating Keys

```python
from cryptography.fernet import Fernet

# Generate a new key
key = Fernet.generate_key()
print(key.decode())  # Use this as APP_SECRET_KEY
```

Or via command line:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Best Practices

### 1. Never Commit Keys

❌ **Don't do this:**
```yaml
# .env (committed to git)
APP_SECRET_KEY=my-secret-key-here
```

✅ **Do this instead:**
```bash
# Set in environment (not committed)
export APP_SECRET_KEY="key-from-vault"
```

### 2. Use Different Keys Per Environment

```bash
# Development
export APP_SECRET_KEY="dev-key-12345..."

# Production (from secret manager)
export APP_SECRET_KEY="$(aws secretsmanager get-secret-value ...)"
```

### 3. Minimize Secret Access

```python
# ❌ Bad: Decrypt early and store
db_password = cfg["database"]["password"].get()
app.config["DB_PASSWORD"] = db_password  # Now in memory as plaintext

# ✅ Good: Decrypt only when needed
def connect_to_db():
    password = cfg["database"]["password"].get()  # Decrypt on use
    return create_connection(password=password)
```

### 4. Rotate Keys Periodically

When rotating encryption keys:

1. Generate new key
2. Decrypt secrets with old key
3. Re-encrypt with new key
4. Update configuration files
5. Deploy new key to environments

### 5. Prefer Environment Variables in Production

For production systems, consider using environment variables directly instead of encrypted config files:

```yaml
# config/application-prod.yml
database:
  password: ${DB_PASSWORD}  # From environment

api:
  key: ${API_KEY}  # From environment
```

---

## Error Handling

```python
from sprigconfig import load_config
from sprigconfig.lazy_secret import LazySecret

cfg = load_config()

try:
    password = cfg["database"]["password"].get()
except Exception as e:
    # Handle decryption errors
    print(f"Failed to decrypt secret: {e}")
```

Common errors:
- **Invalid key**: Key doesn't match the one used for encryption
- **Missing key**: No key provider configured
- **Corrupted ciphertext**: ENC() value is malformed

---

## Examples

See the [Secrets Example](https://gitlab.com/dgw_software/sprig-config/-/tree/main/sprig-config-module/examples/secrets) for complete working code demonstrating:

- Key generation
- Secret encryption
- Configuration file setup
- Decryption patterns
- Best practices

---

## Related Documentation

- [Security Guide](../security.md) - Overall security best practices
- [Best Practices Guide](../../sprig-config-module/docs/SprigConfig_ENC_BestPractices.md) - Detailed encryption patterns
- [Configuration Guide](../configuration.md) - General configuration usage



---

# File: docs/api/utilities.md

# Utilities API

Advanced utilities for configuration management and merging.

## deep_merge()

A utility function for deeply merging nested dictionaries with override semantics.

::: sprigconfig.deepmerge.deep_merge
    options:
      show_root_heading: true
      show_source: true

**Example:**

```python
from sprigconfig import deep_merge

base = {
    "database": {
        "host": "localhost",
        "port": 5432,
        "pool_size": 10
    },
    "features": {
        "analytics": False
    }
}

override = {
    "database": {
        "port": 3306,  # Override
        "ssl": True    # Add new key
    },
    "features": {
        "analytics": True  # Override
    }
}

result = deep_merge(base, override)
# {
#     "database": {
#         "host": "localhost",      # From base
#         "port": 3306,             # Overridden
#         "pool_size": 10,          # From base
#         "ssl": True               # Added from override
#     },
#     "features": {
#         "analytics": True         # Overridden
#     }
# }
```

### Merge Semantics

- **Dictionaries**: Recursively merged (deep merge)
- **Lists**: Replaced entirely (not merged)
- **Scalars**: Override takes precedence
- **Type conflicts**: Override replaces base (e.g., dict → list)

### Advanced Usage

```python
# Merging multiple layers
layer1 = {"a": 1, "b": {"x": 1}}
layer2 = {"b": {"y": 2}}
layer3 = {"b": {"z": 3}, "c": 3}

result = deep_merge(layer1, layer2)
result = deep_merge(result, layer3)
# {"a": 1, "b": {"x": 1, "y": 2, "z": 3}, "c": 3}
```

### When to Use

`deep_merge()` is useful when:

- Building configuration programmatically
- Implementing custom config loaders
- Merging data from multiple sources
- Testing merge behavior

**Note:** SprigConfig uses `deep_merge()` internally for all configuration merging.

---

## ConfigSingleton

A thread-safe singleton for globally shared configuration across your application.

::: sprigconfig.ConfigSingleton
    options:
      show_root_heading: true
      show_source: true
      members:
        - get_instance
        - load
        - reload
        - clear
        - is_loaded

**Example:**

```python
from sprigconfig import ConfigSingleton

# Load configuration once
ConfigSingleton.load(profile="prod")

# Access from anywhere in your application
def my_function():
    cfg = ConfigSingleton.get_instance()
    db_host = cfg.get("database.host")
    return db_host

def another_function():
    cfg = ConfigSingleton.get_instance()
    # Same config instance, no reload
    return cfg.get("app.name")
```

### Thread Safety

`ConfigSingleton` is thread-safe and implements lazy initialization:

```python
import threading
from sprigconfig import ConfigSingleton

def worker():
    # Each thread gets the same config instance
    cfg = ConfigSingleton.get_instance()
    print(cfg.get("app.name"))

# Safe to call from multiple threads
threads = [threading.Thread(target=worker) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### Lifecycle Management

```python
from sprigconfig import ConfigSingleton

# Load configuration
ConfigSingleton.load(profile="dev")

# Check if loaded
if ConfigSingleton.is_loaded():
    cfg = ConfigSingleton.get_instance()

# Reload configuration (e.g., after config file changes)
ConfigSingleton.reload(profile="dev")

# Clear singleton (useful for testing)
ConfigSingleton.clear()
```

### Web Application Pattern

Common pattern for Flask/FastAPI applications:

```python
from flask import Flask
from sprigconfig import ConfigSingleton

def create_app():
    app = Flask(__name__)

    # Load config once at startup
    ConfigSingleton.load(profile="prod")

    # Use throughout request handlers
    @app.route("/api/info")
    def info():
        cfg = ConfigSingleton.get_instance()
        return {
            "app": cfg.get("app.name"),
            "version": cfg.get("app.version")
        }

    return app

app = create_app()
```

### Testing with ConfigSingleton

Clear the singleton between tests to avoid state leakage:

```python
import pytest
from sprigconfig import ConfigSingleton

@pytest.fixture(autouse=True)
def clear_config_singleton():
    """Clear singleton before each test."""
    ConfigSingleton.clear()
    yield
    ConfigSingleton.clear()

def test_my_feature():
    ConfigSingleton.load(profile="test")
    cfg = ConfigSingleton.get_instance()
    assert cfg.get("app.profile") == "test"
```

### When to Use ConfigSingleton

✅ **Good use cases:**
- Web applications (Flask, FastAPI, Django)
- Long-running services
- Applications with many modules
- Avoiding repeated file I/O

❌ **Avoid when:**
- Writing libraries (let consumers manage config)
- Need multiple configurations simultaneously
- Frequent config reloading required
- Testing with different configs in parallel

### Alternative: Direct load_config()

If you don't need global sharing:

```python
from sprigconfig import load_config

# Simple, explicit, no singleton
cfg = load_config(profile="dev")

# Pass config explicitly to functions
def my_function(cfg):
    return cfg.get("database.host")

result = my_function(cfg)
```

---

## Comparison: load_config() vs ConfigSingleton

| Feature | `load_config()` | `ConfigSingleton` |
|---------|-----------------|-------------------|
| **Use case** | Simple scripts, explicit config | Web apps, global sharing |
| **State** | Stateless, creates new `Config` | Singleton, cached globally |
| **Thread safety** | Each call is independent | Shared across threads |
| **Testing** | Easy to test with different configs | Needs cleanup between tests |
| **Overhead** | Reads files on each call | Reads once, caches forever |
| **Recommended for** | Libraries, scripts, tests | Applications, services |

---

## Examples

### Example 1: Manual Config Merging

```python
from sprigconfig import deep_merge

# Load multiple config sources
import yaml

with open("defaults.yml") as f:
    defaults = yaml.safe_load(f)

with open("overrides.yml") as f:
    overrides = yaml.safe_load(f)

# Merge manually
config = deep_merge(defaults, overrides)
```

### Example 2: Application-Wide Config

```python
# app/__init__.py
from sprigconfig import ConfigSingleton

def init_app():
    ConfigSingleton.load(profile="prod")
    print("Configuration loaded")

# app/database.py
from sprigconfig import ConfigSingleton

def get_db_connection():
    cfg = ConfigSingleton.get_instance()
    return connect(
        host=cfg.get("database.host"),
        port=cfg.get("database.port")
    )

# app/api.py
from sprigconfig import ConfigSingleton

def get_api_client():
    cfg = ConfigSingleton.get_instance()
    return APIClient(
        base_url=cfg.get("api.base_url"),
        api_key=cfg.get("api.key").get()
    )
```

### Example 3: Config Reload on Signal

```python
import signal
from sprigconfig import ConfigSingleton

def reload_config(signum, frame):
    print("Reloading configuration...")
    ConfigSingleton.reload()
    print("Configuration reloaded")

# Reload config on SIGHUP
signal.signal(signal.SIGHUP, reload_config)

# Initial load
ConfigSingleton.load(profile="prod")

# Send SIGHUP to reload: kill -HUP <pid>
```

---

## Related Documentation

- [Core API](core.md) - Main configuration loading functions
- [Configuration Guide](../configuration.md) - General configuration usage
- [Examples](https://gitlab.com/dgw_software/sprig-config/-/tree/main/sprig-config-module/examples) - Real-world code samples



---

# File: docs/cli.md

---
layout: default
title: CLI
---

# Command-Line Interface

SprigConfig includes a CLI for inspecting and debugging configuration. This is invaluable for understanding merged configuration, verifying deployments, and troubleshooting issues.

---

## Installation

The CLI is included when you install SprigConfig:

```bash
pip install sprig-config
```

Verify installation:

```bash
sprigconfig --help
```

---

## The `dump` Command

The primary CLI command loads configuration and displays the merged result.

### Basic usage

```bash
sprigconfig dump --config-dir=config --profile=dev
```

This loads configuration from `config/` with the `dev` profile and prints the merged result to stdout.

### Required arguments

| Argument | Description |
|----------|-------------|
| `--config-dir PATH` | Directory containing configuration files |
| `--profile NAME` | Profile to load (dev, test, prod, etc.) |

### Example output

```bash
$ sprigconfig dump --config-dir=config --profile=dev
```

```yaml
app:
  profile: dev
server:
  host: localhost
  port: 9090
database:
  host: localhost
  port: 5432
  password: <LazySecret>
logging:
  level: DEBUG
sprigconfig:
  _meta:
    profile: dev
    sources:
      - /path/to/config/application.yml
      - /path/to/config/application-dev.yml
```

---

## Command Options

### `--format`

Specify the input configuration format:

```bash
# Load YAML files (default)
sprigconfig dump --config-dir=config --profile=dev --format=yml

# Load JSON files
sprigconfig dump --config-dir=config --profile=dev --format=json

# Load TOML files
sprigconfig dump --config-dir=config --profile=dev --format=toml
```

### `--output-format`

Control the output format:

```bash
# Output as YAML (default)
sprigconfig dump --config-dir=config --profile=dev --output-format=yaml

# Output as JSON
sprigconfig dump --config-dir=config --profile=dev --output-format=json
```

### `--output`

Write to a file instead of stdout:

```bash
sprigconfig dump --config-dir=config --profile=prod --output=merged-config.yml
```

### `--secrets`

Reveal decrypted secrets in output:

```bash
# Default: secrets are redacted
$ sprigconfig dump --config-dir=config --profile=prod
database:
  password: <LazySecret>

# With --secrets: plaintext shown (unsafe!)
$ sprigconfig dump --config-dir=config --profile=prod --secrets
database:
  password: actual-plaintext-password
```

**Warning:** Only use `--secrets` in secure environments. Never pipe to logs or shared outputs.

---

## Use Cases

### Verify configuration before deployment

```bash
# Check what production will see
sprigconfig dump --config-dir=config --profile=prod

# Save for review
sprigconfig dump --config-dir=config --profile=prod --output=prod-review.yml
```

### Compare profiles

```bash
# Dump each profile
sprigconfig dump --config-dir=config --profile=dev --output=dev.yml
sprigconfig dump --config-dir=config --profile=prod --output=prod.yml

# Compare
diff dev.yml prod.yml
```

### Debug merge issues

When configuration doesn't look right:

```bash
# See the full merged result
sprigconfig dump --config-dir=config --profile=dev

# Check what files were loaded
sprigconfig dump --config-dir=config --profile=dev | grep -A 20 "_meta"
```

### Validate CI/CD configuration

Add to your CI pipeline:

```yaml
# GitLab CI example
validate-config:
  script:
    - pip install sprig-config
    - sprigconfig dump --config-dir=config --profile=prod
  rules:
    - changes:
        - config/**/*
```

### Generate documentation

Export your configuration structure:

```bash
sprigconfig dump --config-dir=config --profile=dev --output-format=json > docs/config-schema.json
```

---

## Pytest Integration

SprigConfig provides pytest flags for debugging tests:

### `--dump-config`

Print merged configuration for each test:

```bash
pytest --dump-config tests/
```

### `--dump-config-format`

Choose output format:

```bash
pytest --dump-config --dump-config-format=json tests/
```

### `--dump-config-secrets`

Resolve LazySecrets (still redacted by default):

```bash
pytest --dump-config --dump-config-secrets tests/
```

### `--dump-config-no-redact`

Show plaintext secrets (very unsafe):

```bash
pytest --dump-config --dump-config-secrets --dump-config-no-redact tests/
```

### `--debug-dump`

Write merged configuration to a file after tests:

```bash
pytest --debug-dump=test-config-snapshot.yml tests/
```

### `--env-path`

Use a custom `.env` file:

```bash
pytest --env-path=/path/to/.env.test tests/
```

---

## Error Messages

The CLI provides clear error messages:

### Missing configuration directory

```bash
$ sprigconfig dump --config-dir=nonexistent --profile=dev
Error: Configuration directory not found: nonexistent
```

### Missing profile file

```bash
$ sprigconfig dump --config-dir=config --profile=staging
Error: Profile file not found: config/application-staging.yml
```

### Invalid YAML

```bash
$ sprigconfig dump --config-dir=config --profile=dev
Error: Invalid YAML in config/application.yml: ...
```

### Circular import

```bash
$ sprigconfig dump --config-dir=config --profile=dev
Error: Circular import detected: a.yml → b.yml → a.yml
```

---

## Environment Variables

The CLI respects these environment variables:

| Variable | Description |
|----------|-------------|
| `SPRIGCONFIG_FORMAT` | Default config format (yml, json, toml) |
| `APP_SECRET_KEY` | Fernet key for decrypting secrets |

Example:

```bash
export APP_SECRET_KEY="your-fernet-key"
sprigconfig dump --config-dir=config --profile=prod --secrets
```

---

## Scripting Examples

### Check if configuration loads successfully

```bash
#!/bin/bash
if sprigconfig dump --config-dir=config --profile=prod > /dev/null 2>&1; then
    echo "Configuration valid"
    exit 0
else
    echo "Configuration error"
    exit 1
fi
```

### Extract a specific value

```bash
# Using jq with JSON output
PORT=$(sprigconfig dump --config-dir=config --profile=prod --output-format=json | jq -r '.server.port')
echo "Server port: $PORT"
```

### Validate all profiles

```bash
#!/bin/bash
for profile in dev test prod; do
    echo "Checking $profile..."
    if ! sprigconfig dump --config-dir=config --profile=$profile > /dev/null; then
        echo "FAILED: $profile"
        exit 1
    fi
done
echo "All profiles valid"
```

---

## Best Practices

1. **Never use `--secrets` in CI logs** — Secrets would be exposed
2. **Validate configuration in CI** — Catch errors before deployment
3. **Use JSON output for scripting** — Easier to parse programmatically
4. **Review production config before deploy** — Dump and verify
5. **Keep dump outputs out of version control** — They may contain sensitive info

---

[← Back to Documentation](index.md)



---

# File: docs/configuration.md

---
layout: default
title: Configuration
---

# Configuration

This guide covers the core concepts and API for working with SprigConfig.

---

## The Config Object

When you load configuration, SprigConfig returns a `Config` object—an immutable-ish mapping wrapper that provides convenient access patterns.

```python
from sprigconfig import load_config

cfg = load_config(profile="dev")
```

### Dictionary-like access

Config objects support standard dictionary operations:

```python
# Direct key access
port = cfg["server"]["port"]

# Iteration
for key in cfg:
    print(key, cfg[key])

# Length
print(len(cfg))

# Key membership
if "server" in cfg:
    print("Server config found")
```

### Dotted-key access

For deeply nested values, use dotted-key notation:

```python
# These are equivalent
port = cfg["server"]["port"]
port = cfg["server.port"]

# With default value
port = cfg.get("server.port", 8080)

# Check existence
if "server.port" in cfg:
    print("Port configured")
```

### Nested Config objects

When you access a nested dictionary, it's automatically wrapped as a Config object:

```python
server = cfg["server"]  # Returns a Config object
print(server["port"])   # 8080
print(server.get("host", "localhost"))
```

---

## Loading Configuration

### Simple loading

```python
from sprigconfig import load_config

# Load with profile
cfg = load_config(profile="dev")

# Load with custom directory
cfg = load_config(profile="prod", config_dir=Path("/opt/myapp/config"))
```

### Using ConfigLoader

For more control, use `ConfigLoader` directly:

```python
from pathlib import Path
from sprigconfig import ConfigLoader

loader = ConfigLoader(
    config_dir=Path("config"),
    profile="dev",
    ext="yml"  # or "json", "toml"
)
cfg = loader.load()
```

### ConfigLoader parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `config_dir` | `Path` | Directory containing configuration files |
| `profile` | `str` | Active profile (dev, test, prod, etc.) |
| `ext` | `str` | File extension (yml, yaml, json, toml) |

---

## Configuration Formats

SprigConfig supports three configuration formats:

### YAML (default)

```yaml
# application.yml
server:
  port: 8080
  host: localhost
```

### JSON

```json
{
  "server": {
    "port": 8080,
    "host": "localhost"
  }
}
```

### TOML

```toml
[server]
port = 8080
host = "localhost"
```

### Selecting a format

The format is determined by:

1. **Explicit parameter:** `ConfigLoader(ext="json")`
2. **Environment variable:** `SPRIGCONFIG_FORMAT=json`
3. **Default:** `yml`

**Important:** All files in a single load must use the same format. You cannot mix YAML and JSON files.

---

## Environment Variable Expansion

Configuration values can reference environment variables using `${VAR}` syntax:

```yaml
database:
  host: ${DB_HOST}
  port: ${DB_PORT:5432}
  username: ${DB_USER:admin}
```

### Syntax

| Pattern | Behavior |
|---------|----------|
| `${VAR}` | Expands to value of VAR, or remains unexpanded if missing |
| `${VAR:default}` | Expands to value of VAR, or uses default if missing |

### When expansion happens

Environment variables are expanded at load time, before YAML/JSON/TOML parsing.

```bash
export DB_HOST=db.example.com
```

```python
cfg = load_config(profile="prod")
print(cfg["database.host"])  # db.example.com
print(cfg["database.port"])  # 5432 (default used)
```

---

## Metadata

Every loaded configuration includes metadata under `sprigconfig._meta`:

```python
cfg = load_config(profile="dev")

meta = cfg["sprigconfig"]["_meta"]
print(meta["profile"])       # dev
print(meta["sources"])       # List of loaded files
print(meta["import_trace"])  # Import graph details
```

### Metadata fields

| Field | Description |
|-------|-------------|
| `profile` | The active profile |
| `sources` | Ordered list of file paths that were loaded |
| `import_trace` | Detailed import graph with depth and order |

### Using metadata for debugging

```python
# See all files that contributed to this config
for source in cfg["sprigconfig._meta.sources"]:
    print(f"Loaded: {source}")

# Check which profile is active
if cfg["sprigconfig._meta.profile"] == "prod":
    print("Running in production mode")
```

---

## Serialization

### Converting to dictionary

```python
# Get plain dict (secrets redacted)
data = cfg.to_dict()

# Get plain dict with secrets revealed (unsafe!)
data = cfg.to_dict(reveal_secrets=True)
```

### Dumping to YAML/JSON

```python
# Dump to YAML string (secrets redacted)
yaml_str = cfg.dump()

# Dump to JSON string
json_str = cfg.dump(output_format="json")

# Write to file
cfg.dump(Path("config-snapshot.yml"))

# Dump with secrets (unsafe!)
cfg.dump(safe=False)
```

---

## ConfigSingleton

For applications that need global access to configuration, use `ConfigSingleton`:

```python
from sprigconfig import ConfigSingleton

# At application startup (once only)
ConfigSingleton.initialize(
    profile="prod",
    config_dir="config"
)

# From anywhere in your application
def get_database_config():
    cfg = ConfigSingleton.get()
    return {
        "host": cfg["database.host"],
        "port": cfg["database.port"],
    }
```

### Thread safety

`ConfigSingleton` is thread-safe. Multiple threads can call `get()` safely.

### Initialization rules

- `initialize()` must be called exactly once
- Calling `initialize()` twice raises an error
- `get()` before `initialize()` raises an error
- Use `_clear_all()` only in tests

---

## Error Handling

SprigConfig raises `ConfigLoadError` for configuration problems:

```python
from sprigconfig import load_config, ConfigLoadError

try:
    cfg = load_config(profile="prod")
except ConfigLoadError as e:
    print(f"Configuration error: {e}")
```

### Common error causes

| Error | Cause |
|-------|-------|
| Missing file | Required file (e.g., `application-prod.yml`) not found |
| Invalid YAML/JSON/TOML | Syntax error in configuration file |
| Circular import | Import chain creates a cycle |
| Missing secret key | `APP_SECRET_KEY` not set for encrypted values |
| Invalid secret key | Key is not a valid Fernet key |

---

## BOM Handling

SprigConfig automatically handles UTF-8 BOM (Byte Order Mark) in configuration files. Files created on Windows with BOM markers are read correctly without producing malformed keys.

This is handled transparently—you don't need to do anything special.

---

## Best Practices

### Keep base configuration complete

Your `application.yml` should contain all keys with sensible defaults. Profile overlays should only override what's different.

### Use dotted keys for deep access

```python
# Prefer this
port = cfg.get("server.database.connection.port", 5432)

# Over this
port = cfg.get("server", {}).get("database", {}).get("connection", {}).get("port", 5432)
```

### Check metadata in tests

```python
def test_production_config():
    cfg = load_config(profile="prod")
    assert cfg["sprigconfig._meta.profile"] == "prod"
    assert "application-prod.yml" in str(cfg["sprigconfig._meta.sources"])
```

### Don't store Config objects long-term

Load configuration once at startup and pass values to components, rather than passing the Config object around.

---

[← Back to Documentation](index.md)



---

# File: docs/faq.md

---
layout: default
title: FAQ
---

# Frequently Asked Questions

Common questions about SprigConfig, organized by topic.

---

## General

### What is SprigConfig?

SprigConfig is a lightweight, production-grade configuration system for Python applications. It brings Spring Boot-style configuration management to Python with layered YAML loading, profile overlays, recursive imports, secure secret handling, and complete provenance tracking.

### Why not just use environment variables?

Environment variables are great for deployment secrets and simple values, but they don't handle:
- Hierarchical configuration
- Default values with environment-specific overrides
- Configuration validation and debugging
- Provenance tracking (knowing where values came from)

SprigConfig works *with* environment variables (`${VAR}` expansion) while providing structure for complex configuration.

### Why not use a different library like Dynaconf or python-dotenv?

SprigConfig has a specific philosophy:
- **Deterministic behavior** — Same inputs always produce same output
- **Runtime-driven profiles** — Profiles never come from files
- **Complete provenance** — Know where every value originated
- **Security first** — Secrets are encrypted and lazy-decrypted

If these principles align with your needs, SprigConfig is a good fit. Other libraries may be better for different use cases.

### What Python versions are supported?

SprigConfig requires **Python 3.13 or later**.

---

## Profiles

### Why can't I set the profile in YAML files?

This is a core design principle. If profiles came from files, you'd have circular logic:
1. Which file determines the profile?
2. That file might be profile-specific!

Runtime-driven profiles ensure:
- Clear precedence (explicit → env var → pytest → default)
- No ambiguity about which profile is active
- Profiles can't accidentally override themselves

### How do I know which profile is active?

The active profile is always available at `app.profile`:

```python
cfg = load_config()
print(cfg["app.profile"])  # dev, test, or prod
```

Or in metadata:
```python
print(cfg["sprigconfig._meta.profile"])
```

### Can I use custom profile names?

Yes. Use any name you want:

```python
cfg = load_config(profile="staging")
cfg = load_config(profile="qa")
cfg = load_config(profile="local-docker")
```

Just create the corresponding overlay file (e.g., `application-staging.yml`).

### Why does pytest automatically use the "test" profile?

SprigConfig detects pytest execution and defaults to `test` profile. This prevents accidentally running tests with production settings.

Override if needed:
```python
cfg = load_config(profile="dev")  # Explicit override
```

---

## Configuration Files

### What file formats are supported?

- **YAML** (`.yml`, `.yaml`) — Default and recommended
- **JSON** (`.json`) — Strict, portable
- **TOML** (`.toml`) — Python 3.11+ stdlib

### Can I mix formats (e.g., YAML base with JSON overlay)?

No. All files in a single configuration load must use the same format. This is intentional—mixing formats would introduce ambiguity in merge semantics.

### Why isn't INI/Properties format supported?

Flat formats require inventing behavior for:
- Dot-splitting keys into hierarchy
- List coercion
- Type inference

This invented behavior would violate SprigConfig's principle of explicit, predictable configuration. See [Philosophy](philosophy.md) for details.

### How do I switch between formats?

```python
# Via parameter
loader = ConfigLoader(config_dir=Path("config"), profile="dev", ext="json")

# Via environment variable
export SPRIGCONFIG_FORMAT=json
```

---

## Merging

### Why do lists replace instead of append?

List appending creates ambiguity:
- What if you want to remove items?
- What's the order of appended items?
- How do you clear a list?

Replacement is explicit: you see exactly what the final list contains. If you want all items from base plus overlay, include them all in the overlay.

### How do I debug merge issues?

1. **Use the CLI:**
   ```bash
   sprigconfig dump --config-dir=config --profile=dev
   ```

2. **Check metadata:**
   ```python
   for source in cfg["sprigconfig._meta.sources"]:
       print(f"Loaded: {source}")
   ```

3. **Enable logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### What are "collision warnings"?

SprigConfig warns when an overlay might unintentionally lose keys. For example, if base has five keys and overlay mentions two, you'll see a warning.

Suppress if intentional:
```yaml
suppress_config_merge_warnings: true
```

---

## Imports

### Can imports create circular references?

No. SprigConfig detects cycles and raises `ConfigLoadError` with a clear message showing the cycle path.

### Can I import from parent directories?

No. Imports cannot escape the configuration directory. Path traversal like `../secrets.yml` is blocked for security.

### What's the difference between root and positional imports?

**Root imports** merge at the configuration root:
```yaml
imports:
  - database.yml  # Merges at root level
```

**Positional imports** merge at their location:
```yaml
database:
  imports:
    - connection.yml  # Merges under database:
```

---

## Secrets

### How secure is the encryption?

SprigConfig uses **Fernet encryption** from the `cryptography` library. Fernet provides:
- AES-128-CBC encryption
- HMAC-SHA256 authentication
- Timestamp validation

This is industry-standard symmetric encryption suitable for configuration secrets.

### What happens if I lose the encryption key?

Encrypted values cannot be recovered without the key. This is by design—there's no backdoor.

Best practices:
- Store keys in secret managers with backup
- Document key locations
- Test key recovery procedures

### Can I use different keys for different environments?

Yes, and you should. Generate a separate key for each environment to limit blast radius if a key is compromised.

### Why are secrets "lazy"?

Lazy decryption means:
- Secrets stay encrypted in memory until needed
- You control when decryption happens
- Logging configuration won't accidentally expose secrets
- Failed decryption is caught at point of use

---

## Performance

### Is SprigConfig slow?

Configuration is typically loaded once at application startup. SprigConfig's loading time is negligible for most applications.

If you're loading configuration in a hot path, use `ConfigSingleton` to load once and reuse.

### Does SprigConfig cache configuration?

`ConfigSingleton` caches the loaded configuration. Direct `load_config()` calls load fresh each time.

### Is ConfigSingleton thread-safe?

Yes. `ConfigSingleton` uses locking to ensure thread-safe initialization and access.

---

## Troubleshooting

### "ConfigLoadError: Profile file not found"

The profile overlay file doesn't exist:
```
application-staging.yml not found
```

Either create the file or use a different profile.

### "ConfigLoadError: No Fernet key available"

Set the encryption key before loading:
```bash
export APP_SECRET_KEY="your-key"
```

Or in code:
```python
from sprigconfig.lazy_secret import set_global_key
set_global_key("your-key")
```

### "ConfigLoadError: Circular import detected"

Your imports form a cycle. Check the error message for the cycle path and break it.

### "app.profile in YAML is ignored"

This is expected behavior. Remove `app.profile` from your YAML files—runtime determines the profile.

### Windows BOM characters in keys

SprigConfig handles this automatically. Files are read with `utf-8-sig` encoding which strips BOM markers.

---

## Integration

### Can I use SprigConfig with Pydantic?

Yes. Load configuration, then validate with Pydantic:

```python
from pydantic import BaseModel
from sprigconfig import load_config

class DatabaseConfig(BaseModel):
    host: str
    port: int
    pool_size: int

cfg = load_config(profile="prod")
db_config = DatabaseConfig(**cfg["database"])
```

### Can I use SprigConfig with FastAPI?

Yes:

```python
from fastapi import FastAPI
from sprigconfig import ConfigSingleton

ConfigSingleton.initialize(profile="prod", config_dir="config")

app = FastAPI()

@app.get("/config")
def get_config():
    cfg = ConfigSingleton.get()
    return {"port": cfg["server.port"]}
```

### Can I use SprigConfig with Django?

Yes, in `settings.py`:

```python
from sprigconfig import load_config

cfg = load_config(profile=os.getenv("DJANGO_ENV", "dev"))

DEBUG = cfg.get("django.debug", False)
DATABASES = {
    "default": {
        "HOST": cfg["database.host"],
        "PORT": cfg["database.port"],
    }
}
```

---

## Contributing

### How do I report bugs?

Open an issue at [GitLab](https://gitlab.com/dgw_software/sprig-config/-/issues) with:
- What you expected
- What happened
- Relevant configuration (redacted if needed)
- Python version

### Can I add support for new formats?

Format support may be considered if:
- There's demonstrated demand
- The format natively expresses hierarchy
- Semantics are explicit and documented

See [CONTRIBUTING.md](https://gitlab.com/dgw_software/sprig-config/-/blob/main/sprig-config-module/CONTRIBUTING.md) for guidelines.

---

[← Back to Documentation](index.md)



---

# File: docs/getting-started.md

---
layout: default
title: Getting Started
---

# Getting Started

This guide walks you through installing SprigConfig and loading your first configuration.

---

## Installation

Install SprigConfig from PyPI:

```bash
pip install sprig-config
```

Or with Poetry:

```bash
poetry add sprig-config
```

**Requirements:** Python 3.13 or later.

---

## Project Setup

Create a `config/` directory in your project root:

```
my-project/
├── config/
│   ├── application.yml
│   ├── application-dev.yml
│   ├── application-test.yml
│   └── application-prod.yml
├── src/
│   └── ...
└── pyproject.toml
```

---

## Your First Configuration

### Base configuration

Create `config/application.yml` with shared defaults:

```yaml
# config/application.yml
server:
  host: localhost
  port: 8080

database:
  pool_size: 5
  timeout: 30

logging:
  level: INFO
  format: "%(levelname)s - %(message)s"
```

### Development overlay

Create `config/application-dev.yml` for development overrides:

```yaml
# config/application-dev.yml
server:
  port: 9090

logging:
  level: DEBUG
```

### Production overlay

Create `config/application-prod.yml` for production:

```yaml
# config/application-prod.yml
server:
  host: 0.0.0.0

database:
  pool_size: 20

logging:
  level: INFO
```

---

## Loading Configuration

### Basic usage

```python
from sprigconfig import load_config

# Load with explicit profile
cfg = load_config(profile="dev")

# Access values
print(cfg["server"]["port"])      # 9090
print(cfg["server"]["host"])      # localhost
print(cfg["database"]["pool_size"])  # 5
```

### Dotted-key access

SprigConfig supports convenient dotted-key notation:

```python
# These are equivalent
port = cfg["server"]["port"]
port = cfg["server.port"]
port = cfg.get("server.port")

# With default value
port = cfg.get("server.port", 8080)
```

### Check if key exists

```python
if "server.port" in cfg:
    print("Port is configured")
```

---

## Profile Selection

Profiles are determined at runtime in this order:

1. **Explicit parameter:** `load_config(profile="prod")`
2. **Environment variable:** `APP_PROFILE=prod`
3. **pytest context:** Automatically uses `"test"`
4. **Default:** Falls back to `"dev"`

The active profile is always available in the config:

```python
print(cfg["app.profile"])  # dev, test, or prod
```

**Important:** Never set `app.profile` in your YAML files. SprigConfig ignores it with a warning.

---

## Configuration Directory

By default, SprigConfig looks for `config/` in your project root. You can customize this:

### Via parameter

```python
from pathlib import Path
cfg = load_config(profile="dev", config_dir=Path("/opt/myapp/config"))
```

### Via environment variable

```bash
export APP_CONFIG_DIR=/opt/myapp/config
```

### Via .env file

Create a `.env` file in your project root:

```
APP_CONFIG_DIR=/opt/myapp/config
APP_PROFILE=dev
```

---

## Using ConfigLoader (Modern API)

For more control, use the `ConfigLoader` class directly:

```python
from pathlib import Path
from sprigconfig import ConfigLoader

loader = ConfigLoader(
    config_dir=Path("config"),
    profile="dev"
)
cfg = loader.load()
```

---

## Using ConfigSingleton (Application Pattern)

For applications that need global access to configuration:

```python
from sprigconfig import ConfigSingleton

# Initialize once at startup
ConfigSingleton.initialize(profile="prod", config_dir="config")

# Access from anywhere in your application
cfg = ConfigSingleton.get()
print(cfg["database.pool_size"])
```

**Note:** `initialize()` can only be called once. Subsequent calls raise an error.

---

## Environment Variable Expansion

Configuration values can reference environment variables:

```yaml
# config/application.yml
database:
  host: ${DB_HOST}
  port: ${DB_PORT:5432}    # Default to 5432 if not set
  password: ${DB_PASSWORD}
```

```bash
export DB_HOST=db.example.com
export DB_PASSWORD=secret
```

```python
cfg = load_config(profile="prod")
print(cfg["database.host"])  # db.example.com
print(cfg["database.port"])  # 5432 (default)
```

---

## What's Next?

Now that you have basic configuration working:

- [Configuration](configuration.md) — Learn about the Config object and API
- [Merge Order](merge-order.md) — Understand how layering works
- [Profiles](profiles.md) — Deep dive into profile management
- [Imports](imports.md) — Modularize your configuration
- [Security](security.md) — Handle sensitive values securely

---

[← Back to Documentation](index.md)



---

# File: docs/imports.md

---
layout: default
title: Imports
---

# Imports

SprigConfig supports recursive configuration imports, allowing you to modularize large configurations into manageable, reusable pieces.

---

## Basic Imports

Use the `imports:` directive to include other configuration files:

```yaml
# application.yml
server:
  port: 8080

imports:
  - database.yml
  - logging.yml
  - features.yml
```

Each imported file is merged into the configuration at the point where the import appears.

---

## Import Resolution

### File paths

Import paths are relative to the configuration directory:

```
config/
├── application.yml
├── database.yml
├── logging.yml
└── features/
    ├── auth.yml
    └── caching.yml
```

```yaml
# application.yml
imports:
  - database.yml
  - logging.yml
  - features/auth.yml
  - features/caching.yml
```

### Extension handling

Import paths can omit the file extension. SprigConfig automatically appends the active format's extension:

```yaml
# With yml format active
imports:
  - database     # Resolves to database.yml
  - logging      # Resolves to logging.yml
```

If you specify an extension, it must match the active format:

```yaml
imports:
  - database.yml  # OK with yml format
  - database.json # Error if yml format is active
```

### Subdirectories

Organize related configuration in subdirectories:

```yaml
imports:
  - common/defaults
  - security/policies
  - integrations/aws
```

---

## Import Order

Files are processed in the order they appear in the `imports:` list:

```yaml
imports:
  - a.yml    # Loaded first
  - b.yml    # Merged on top of a.yml
  - c.yml    # Merged on top of result
```

Later imports can override values from earlier imports.

### Recursive imports

Imported files can themselves have imports:

```yaml
# application.yml
imports:
  - database.yml

# database.yml
database:
  driver: postgresql
imports:
  - database-pools.yml

# database-pools.yml
database:
  pool_size: 10
```

SprigConfig processes these depth-first:
1. Load `database.yml`
2. Recursively load `database-pools.yml` and merge
3. Merge result into `application.yml`

---

## Positional Imports

Imports can appear at any level in the configuration tree, not just at the root:

```yaml
# application.yml
server:
  port: 8080
  imports:
    - server-defaults.yml

database:
  imports:
    - database-defaults.yml
```

### How positional imports work

When imports appear under a key, the imported content merges at that level:

```yaml
# server-defaults.yml (imported under server:)
host: localhost
timeout: 30
ssl: false

# Result
server:
  port: 8080
  host: localhost
  timeout: 30
  ssl: false
```

This is different from root-level imports where content merges at the root.

### Nested example

```yaml
# application.yml
app:
  features:
    imports:
      - feature-flags.yml

# feature-flags.yml
new_ui: true
beta_api: false
dark_mode: true

# Result
app:
  features:
    new_ui: true
    beta_api: false
    dark_mode: true
```

---

## Circular Import Detection

SprigConfig detects and prevents circular imports:

```yaml
# a.yml
imports:
  - b.yml

# b.yml
imports:
  - a.yml  # Creates a cycle!
```

This raises `ConfigLoadError` with a clear message about the cycle.

### Cycle detection is path-based

The same file can be imported from different paths as long as no cycle forms:

```yaml
# application.yml
imports:
  - shared.yml

# application-dev.yml
imports:
  - shared.yml  # OK - not a cycle

# This is fine because they're parallel imports, not circular
```

---

## Security Restrictions

### Path traversal prevention

Imports cannot escape the configuration directory:

```yaml
imports:
  - ../secrets.yml           # Blocked
  - /etc/passwd              # Blocked
  - ../../other-project.yml  # Blocked
```

SprigConfig raises `ConfigLoadError` for any path traversal attempts.

### Absolute paths

Absolute paths are not allowed:

```yaml
imports:
  - /opt/config/shared.yml  # Blocked
```

All imports must be relative to the configuration directory.

---

## Import Trace

Every loaded configuration includes an import trace in its metadata:

```python
cfg = load_config(profile="dev")

trace = cfg["sprigconfig._meta.import_trace"]
for entry in trace:
    print(f"File: {entry['file']}")
    print(f"Depth: {entry['depth']}")
    print(f"Order: {entry['order']}")
```

The trace shows:
- Which files were imported
- The depth in the import tree
- The order they were processed

This helps debug complex import hierarchies.

---

## Common Patterns

### Shared defaults

```yaml
# config/common/defaults.yml
logging:
  format: "%(levelname)s - %(message)s"
  handlers:
    - console
    - file

# config/application.yml
imports:
  - common/defaults.yml

logging:
  level: INFO
```

### Environment-specific overrides

```yaml
# config/application.yml
imports:
  - common/base.yml

# config/application-prod.yml
imports:
  - environments/production.yml
```

### Feature modules

```yaml
# config/application.yml
imports:
  - features/auth.yml
  - features/caching.yml
  - features/notifications.yml
```

### Layered security

```yaml
# config/application.yml
imports:
  - security/defaults.yml

# config/application-prod.yml
imports:
  - security/hardened.yml
```

---

## Import Behavior with Profiles

Both base and profile files can have imports:

```yaml
# application.yml
imports:
  - common/base.yml

# application-prod.yml
imports:
  - production/settings.yml
```

Processing order:
1. `application.yml`
2. Imports from `application.yml`
3. `application-<profile>.yml`
4. Imports from `application-<profile>.yml`

Profile imports are processed last, giving them final override priority.

---

## Best Practices

### Keep imports organized

```
config/
├── application.yml
├── application-dev.yml
├── application-prod.yml
├── common/
│   ├── database.yml
│   └── logging.yml
├── features/
│   ├── auth.yml
│   └── caching.yml
└── environments/
    ├── development.yml
    └── production.yml
```

### Avoid deep import chains

While SprigConfig supports deep recursion, deeply nested imports are hard to debug:

```yaml
# Harder to follow
a.yml → b.yml → c.yml → d.yml → e.yml

# Easier to follow
application.yml
├── common.yml
├── features.yml
└── environment.yml
```

### Use positional imports for related config

```yaml
# Good: related config together
database:
  imports:
    - database/connection.yml
    - database/pools.yml

# Less clear: scattered at root
imports:
  - database-connection.yml
  - database-pools.yml
  - unrelated-stuff.yml
```

### Document your import structure

Add comments explaining the import hierarchy:

```yaml
# Base configuration with common defaults
# See: common/README.md for import structure
imports:
  - common/logging.yml     # Logging defaults
  - common/security.yml    # Security policies
  - features/index.yml     # Feature configuration
```

---

[← Back to Documentation](index.md)



---

# File: docs/index.md

---
layout: default
title: SprigConfig
---

# SprigConfig

**Spring Boot-style configuration for Python applications.**

SprigConfig is a lightweight, production-grade configuration system that brings layered YAML loading, profile overlays, recursive imports, secure secret handling, and complete provenance tracking to Python.

---

## Why SprigConfig?

Configuration should be **predictable**, **debuggable**, and **secure**. SprigConfig is designed to make configuration behavior easier to reason about—especially at 3am during an outage.

- **Layered configuration** with deterministic deep merge semantics
- **Runtime-driven profiles** (dev, test, prod) that never come from files
- **Recursive imports** with cycle detection
- **Encrypted secrets** that stay encrypted until you need them
- **Complete provenance tracking** so you know where every value came from

---

## Quick Example

```yaml
# config/application.yml
server:
  port: 8080
  host: localhost

logging:
  level: INFO
```

```yaml
# config/application-dev.yml
server:
  port: 9090

logging:
  level: DEBUG
```

```python
from sprigconfig import load_config

cfg = load_config(profile="dev")
print(cfg["server.port"])    # 9090 (from dev overlay)
print(cfg["server.host"])    # localhost (from base)
print(cfg["app.profile"])    # dev (injected at runtime)
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| [Profile Overlays](profiles.md) | Environment-specific configuration without code changes |
| [Deep Merge](merge-order.md) | Predictable layering with collision warnings |
| [Recursive Imports](imports.md) | Modular configuration with `imports:` directive |
| [Secure Secrets](security.md) | Fernet-encrypted values with lazy decryption |
| [CLI Tools](cli.md) | Inspect and debug merged configuration |
| [Provenance Tracking](configuration.md#metadata) | Know where every value came from |

---

## Installation

```bash
pip install sprig-config
```

Or with Poetry:

```bash
poetry add sprig-config
```

**Requirements:** Python 3.13+

---

## Supported Formats

SprigConfig supports multiple configuration formats:

| Format | Extensions | Notes |
|--------|------------|-------|
| YAML | `.yml`, `.yaml` | Default and recommended |
| JSON | `.json` | Strict, portable |
| TOML | `.toml` | Uses Python 3.11+ stdlib |

All files in a single configuration load must use the same format.

---

## Documentation

- [Philosophy](philosophy.md) — Design principles and goals
- [Getting Started](getting-started.md) — Installation and first steps
- [Configuration](configuration.md) — Core concepts and API
- [Merge Order](merge-order.md) — How layering works
- [Profiles](profiles.md) — Environment-specific overlays
- [Imports](imports.md) — Modular configuration
- [CLI](cli.md) — Command-line tools
- [Security](security.md) — Secret management
- [FAQ](faq.md) — Common questions
- [Roadmap](roadmap.md) — Future plans

---

## Project Links

- **Source (GitLab):** [gitlab.com/dgw_software/sprig-config](https://gitlab.com/dgw_software/sprig-config)
- **Mirror (GitHub):** [github.com/dgw_software/sprig-config](https://github.com/dgw_software/sprig-config)
- **PyPI:** [pypi.org/project/sprigconfig](https://pypi.org/project/sprigconfig/)

---

## License

MIT License. See [LICENSE](https://gitlab.com/dgw_software/sprig-config/-/blob/main/LICENSE) for details.



---

# File: docs/merge-order.md

---
layout: default
title: Merge Order
---

# Merge Order

Understanding how SprigConfig merges configuration files is essential for predictable behavior. This guide explains the merge order, deep merge semantics, and how to debug merge issues.

---

## Merge Sequence

SprigConfig loads and merges configuration in this exact order:

```
1. application.<ext>           ← Base configuration
2. Base imports                ← Files from base's imports: directive
3. application-<profile>.<ext> ← Profile overlay
4. Profile imports             ← Files from profile's imports: directive
```

Each step merges into the result of the previous step.

### Visual example

Given these files:

```yaml
# application.yml
server:
  port: 8080
  host: localhost
imports:
  - defaults.yml

# defaults.yml
server:
  timeout: 30

# application-dev.yml
server:
  port: 9090
imports:
  - dev-extras.yml

# dev-extras.yml
server:
  debug: true
```

The merge happens as:

1. Load `application.yml` → `{server: {port: 8080, host: localhost}}`
2. Merge `defaults.yml` → `{server: {port: 8080, host: localhost, timeout: 30}}`
3. Merge `application-dev.yml` → `{server: {port: 9090, host: localhost, timeout: 30}}`
4. Merge `dev-extras.yml` → `{server: {port: 9090, host: localhost, timeout: 30, debug: true}}`

**Key insight:** Profile overlays have the final say. Values in `application-dev.yml` override imported values from `defaults.yml`.

---

## Deep Merge Algorithm

SprigConfig uses a recursive deep merge algorithm with these rules:

### Dictionary + Dictionary

Dictionaries are merged recursively. Keys from both are preserved, with the overlay taking precedence for conflicts.

```yaml
# base
server:
  host: localhost
  port: 8080

# overlay
server:
  port: 9090
  timeout: 30

# result
server:
  host: localhost    # from base
  port: 9090         # from overlay (overrides)
  timeout: 30        # from overlay (new)
```

### List + List

Lists are **completely replaced**, not appended.

```yaml
# base
features:
  - auth
  - logging

# overlay
features:
  - caching

# result
features:
  - caching    # overlay replaces entire list
```

If you want to extend a list, you must repeat all items in the overlay.

### Scalar + Scalar

Scalar values (strings, numbers, booleans) are replaced.

```yaml
# base
port: 8080

# overlay
port: 9090

# result
port: 9090
```

### Missing keys in overlay

Keys present in the base but missing in the overlay are preserved.

```yaml
# base
server:
  host: localhost
  port: 8080

# overlay
server:
  port: 9090
  # host is not mentioned

# result
server:
  host: localhost   # preserved from base
  port: 9090        # from overlay
```

---

## Collision Warnings

SprigConfig warns when overlays might unintentionally lose keys. These warnings help catch configuration mistakes.

### Partial override warning

When an overlay provides only some keys from a nested structure:

```yaml
# base
database:
  host: localhost
  port: 5432
  username: admin
  password: secret

# overlay
database:
  host: db.prod.com
  # port, username, password not mentioned
```

SprigConfig logs a warning indicating that `database` is being partially overridden. The other keys are preserved, but the warning helps catch cases where you might have forgotten to include them.

### Suppressing warnings

If your partial override is intentional, you can suppress warnings:

```yaml
# application.yml
suppress_config_merge_warnings: true
```

Or per-section in your code when using `deep_merge` directly:

```python
from sprigconfig import deep_merge

result = deep_merge(base, overlay, suppress=True)
```

---

## Merge Order With Imports

Imports are processed depth-first as they're encountered. Within an imports list, files are processed in order.

```yaml
# application.yml
imports:
  - a.yml
  - b.yml
```

Processing order:
1. Load `application.yml`
2. Load `a.yml` and merge
3. If `a.yml` has imports, process them recursively
4. Load `b.yml` and merge
5. If `b.yml` has imports, process them recursively

### Positional imports

Imports can appear at any level in the configuration tree:

```yaml
# application.yml
server:
  imports:
    - server-defaults.yml

database:
  imports:
    - database-defaults.yml
```

When imports appear under a key (like `server`), the imported content merges at that level, not at the root.

```yaml
# server-defaults.yml
port: 8080
host: localhost

# Results in:
server:
  port: 8080
  host: localhost
```

---

## Debugging Merge Issues

### Use the CLI

The easiest way to see the final merged result:

```bash
sprigconfig dump --config-dir=config --profile=dev
```

### Check metadata

The merged config includes information about what was loaded:

```python
cfg = load_config(profile="dev")

# See all source files
for source in cfg["sprigconfig._meta.sources"]:
    print(f"Loaded: {source}")

# See the import trace
import_trace = cfg["sprigconfig._meta.import_trace"]
```

### Enable logging

SprigConfig logs merge operations. Enable debug logging to see details:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

You'll see messages like:
- Which files are being loaded
- Override collision warnings
- Import resolution

---

## Common Patterns

### Layered defaults

Use a `defaults.yml` file imported by the base configuration:

```yaml
# application.yml
imports:
  - defaults.yml

# Only specify what's different from defaults
server:
  host: myapp.example.com
```

### Environment-specific databases

Keep database credentials in profile files:

```yaml
# application.yml
database:
  driver: postgresql
  pool_size: 5

# application-prod.yml
database:
  host: ${DB_HOST}
  password: ENC(...)
  pool_size: 20
```

### Feature flags by profile

```yaml
# application.yml
features:
  new_ui: false
  beta_api: false

# application-dev.yml
features:
  new_ui: true
  beta_api: true

# application-prod.yml
features:
  new_ui: true    # Rolled out to production
  beta_api: false # Not yet in production
```

---

## Key Points

1. **Profile overlays win** — They're loaded last and override everything
2. **Lists replace, don't append** — Include all items you want
3. **Deep merge preserves** — Keys not mentioned in overlays are kept
4. **Order is deterministic** — Same inputs always produce same output
5. **Warnings help** — Pay attention to collision warnings

---

[← Back to Documentation](index.md)



---

# File: docs/philosophy.md

---
layout: default
title: Philosophy
---

# Philosophy

SprigConfig is built on a set of guiding principles that inform every design decision. Understanding these principles helps you use the library effectively and predict its behavior.

---

## Core Principles

### 1. Config behavior is more important than file format

What your configuration *does* matters more than *how* it's written. SprigConfig focuses on predictable, deterministic behavior regardless of whether you use YAML, JSON, or TOML.

The merge algorithm, import resolution, and secret handling work identically across all formats. Parsing is treated as a leaf concern—a detail that shouldn't affect configuration semantics.

### 2. Parsing is a leaf concern

SprigConfig separates **configuration behavior** (merging, profiles, imports) from **file parsing**. This means:

- Adding a new format doesn't change how merging works
- Debugging focuses on configuration values, not parser quirks
- The same tests validate behavior across all formats

### 3. Backward compatibility is sacred in 1.x

Every 1.x release maintains backward compatibility with previous 1.x releases. Existing projects continue to work without changes. Breaking changes are reserved for 2.0.

### 4. 2.0 only when contracts change

A major version bump happens only when public APIs or documented behavior must change. We avoid version inflation—2.0 means something significant changed.

---

## Design Philosophy

### Explicit over implicit

Configuration behavior should be obvious from looking at the files. SprigConfig avoids magic that makes configuration hard to understand.

- Profiles are always set at runtime, never from files
- Import order is explicit in the `imports:` list
- Override collisions generate warnings

### Deterministic over convenient

Given the same inputs, SprigConfig always produces the same output. There are no race conditions, random behaviors, or order-dependent surprises.

- Merge order is documented and consistent
- Import resolution follows explicit rules
- Metadata tracks exactly what was loaded

### Traceability over minimalism

Every configuration value should be traceable to its source. SprigConfig injects metadata that tells you:

- Which files were loaded
- In what order they were merged
- What the active profile is
- The complete import graph

This makes debugging configuration issues straightforward—you can see exactly where each value came from.

### Debuggable at 3am

When something goes wrong in production, you need to understand your configuration quickly. SprigConfig is designed to make this easy:

- Clear error messages that identify the source
- CLI tools for inspecting merged configuration
- Provenance tracking in every loaded config
- Collision warnings that help catch mistakes

---

## What SprigConfig Is Not

SprigConfig is intentionally focused. It does not:

- **Validate schemas** — Use Pydantic or similar for validation
- **Manage environment variables** — Use python-dotenv or similar
- **Handle remote configuration** — It loads local files only
- **Support hot reloading** — Configuration is loaded once at startup

This focus allows SprigConfig to do its core job exceptionally well.

---

## Supported Formats

SprigConfig supports formats that **natively express hierarchical configuration**:

| Format | Supported | Reason |
|--------|-----------|--------|
| YAML | Yes | Native hierarchy, comments, readability |
| JSON | Yes | Strict, portable, tooling support |
| TOML | Yes | Modern, stdlib support in Python 3.11+ |
| INI | No | Flat format requiring invented semantics |
| Properties | No | Flat format requiring dot-splitting |

Flat formats are not supported because they would require inventing behavior for:
- Dot-splitting keys into hierarchy
- List coercion rules
- Type inference

This invented behavior would violate the principle that configuration behavior should be explicit and predictable.

---

## Contributing Considerations

When contributing to SprigConfig, keep these principles in mind:

1. **Preserve existing behavior** unless explicitly changing it
2. **Avoid format-specific logic** in core paths
3. **Include tests** that validate behavior across formats
4. **Choose clarity** over cleverness
5. **Document behavior** that affects configuration semantics

See [CONTRIBUTING.md](https://gitlab.com/dgw_software/sprig-config/-/blob/main/sprig-config-module/CONTRIBUTING.md) for detailed guidelines.

---

[← Back to Documentation](index.md)



---

# File: docs/profiles.md

---
layout: default
title: Profiles
---

# Profiles

Profiles allow you to maintain environment-specific configuration without code changes. SprigConfig's profile system is **runtime-driven**—profiles are never read from configuration files.

---

## How Profiles Work

A profile determines which overlay file is loaded on top of the base configuration:

| Profile | Overlay File |
|---------|--------------|
| `dev` | `application-dev.yml` |
| `test` | `application-test.yml` |
| `prod` | `application-prod.yml` |
| `staging` | `application-staging.yml` |
| `<custom>` | `application-<custom>.yml` |

The base `application.yml` is always loaded first, then the profile overlay is merged on top.

---

## Profile Selection

Profiles are determined at runtime in this order:

### 1. Explicit parameter (highest priority)

```python
cfg = load_config(profile="prod")
```

### 2. Environment variable

```bash
export APP_PROFILE=prod
```

```python
cfg = load_config()  # Uses "prod" from environment
```

### 3. pytest context

When running under pytest, SprigConfig automatically uses the `test` profile:

```python
# In test files, profile defaults to "test"
def test_something():
    cfg = load_config()  # Uses "test" profile
    assert cfg["app.profile"] == "test"
```

### 4. Default

If nothing else is specified, SprigConfig uses `dev`.

---

## Profile Injection

The active profile is always injected into the final configuration at `app.profile`:

```python
cfg = load_config(profile="prod")
print(cfg["app.profile"])  # prod
```

This allows your application to know which profile is active at runtime.

### Never set app.profile in files

**Important:** Do not set `app.profile` in your YAML files. SprigConfig ignores it with a warning:

```yaml
# DON'T DO THIS - will be ignored
app:
  profile: dev
```

The runtime always determines the profile, ensuring consistency between what's loaded and what's reported.

---

## Standard Profiles

While you can use any profile name, these are the conventional profiles:

### `dev` — Development

Local development environment with debug settings:

```yaml
# application-dev.yml
server:
  port: 9090

logging:
  level: DEBUG

features:
  hot_reload: true
  debug_toolbar: true
```

### `test` — Testing

Isolated configuration for automated tests:

```yaml
# application-test.yml
database:
  url: sqlite:///:memory:

logging:
  level: WARNING

features:
  email: false  # Don't send real emails in tests
```

### `prod` — Production

Production-hardened configuration:

```yaml
# application-prod.yml
server:
  host: 0.0.0.0

database:
  pool_size: 20
  ssl: true

logging:
  level: INFO

features:
  debug_toolbar: false
```

---

## Production Guardrails

SprigConfig includes safety checks for production:

### Required production file

When using the `prod` profile, `application-prod.yml` must exist. This prevents accidentally running with dev settings in production.

```python
# Raises ConfigLoadError if application-prod.yml is missing
cfg = load_config(profile="prod")
```

### DEBUG logging protection

DEBUG logging in production is blocked by default:

```yaml
# application-prod.yml
logging:
  level: DEBUG  # Blocked unless allow_debug_in_prod is set
```

To allow DEBUG in production (not recommended):

```yaml
# application-prod.yml
allow_debug_in_prod: true
logging:
  level: DEBUG
```

### Default logging level

If no logging level is specified in production, SprigConfig defaults to `INFO`.

---

## Custom Profiles

You can create profiles for any environment:

```yaml
# application-staging.yml
database:
  host: staging-db.example.com

# application-qa.yml
features:
  test_accounts: true

# application-local.yml
server:
  port: 3000
```

Load them by name:

```python
cfg = load_config(profile="staging")
cfg = load_config(profile="qa")
cfg = load_config(profile="local")
```

---

## Profile-Specific Imports

Each profile can have its own imports:

```yaml
# application.yml
server:
  port: 8080
imports:
  - common/logging.yml
  - common/security.yml

# application-dev.yml
imports:
  - dev/mock-services.yml
  - dev/debug-settings.yml

# application-prod.yml
imports:
  - prod/monitoring.yml
  - prod/security-hardening.yml
```

Import order:
1. Base file
2. Base imports
3. Profile file
4. Profile imports

See [Merge Order](merge-order.md) for details.

---

## Checking Profile at Runtime

Use the injected `app.profile` to make runtime decisions:

```python
cfg = load_config()

if cfg["app.profile"] == "prod":
    # Production-specific initialization
    setup_monitoring()
    enable_rate_limiting()
elif cfg["app.profile"] == "dev":
    # Development helpers
    enable_debug_toolbar()
```

Or access from metadata:

```python
profile = cfg["sprigconfig._meta.profile"]
```

---

## Testing with Profiles

### Explicit test profile

```python
def test_production_config():
    cfg = load_config(profile="prod", config_dir=Path("tests/config"))
    assert cfg["database.ssl"] == True
```

### Using pytest fixtures

```python
import pytest
from sprigconfig import load_config

@pytest.fixture
def prod_config():
    return load_config(profile="prod")

def test_pool_size(prod_config):
    assert prod_config["database.pool_size"] >= 10
```

### Environment variable in tests

```python
import os

def test_with_custom_profile(monkeypatch):
    monkeypatch.setenv("APP_PROFILE", "staging")
    cfg = load_config()
    assert cfg["app.profile"] == "staging"
```

---

## Best Practices

### Keep base complete

Your `application.yml` should define all keys with sensible defaults. Profiles should only override what's different.

```yaml
# application.yml - complete defaults
server:
  host: localhost
  port: 8080
  timeout: 30
  max_connections: 100

# application-prod.yml - only overrides
server:
  host: 0.0.0.0
  max_connections: 1000
```

### Don't duplicate across profiles

If a value is the same in dev and test, keep it in the base file.

### Use environment variables for secrets

Don't hardcode credentials in profile files:

```yaml
# application-prod.yml
database:
  password: ${DB_PASSWORD}  # Or use ENC() for encrypted values
```

### Test all profiles

Ensure each profile loads successfully:

```python
@pytest.mark.parametrize("profile", ["dev", "test", "prod"])
def test_profile_loads(profile):
    cfg = load_config(profile=profile)
    assert cfg["app.profile"] == profile
```

---

[← Back to Documentation](index.md)



---

# File: docs/roadmap.md

---
layout: default
title: Roadmap
---

# Roadmap

SprigConfig follows a phased development approach, prioritizing stability and backward compatibility. This roadmap outlines planned features and the principles guiding development.

---

## Guiding Principles

These principles inform all development decisions:

1. **Config behavior > file format** — What configuration does matters more than how it's written
2. **Parsing is a leaf concern** — Format handling is separate from configuration semantics
3. **Backward compatibility is sacred in 1.x** — Existing projects continue to work
4. **2.0 only when contracts change** — Major versions are reserved for breaking changes

Any change violating these principles is either deferred or reserved for a major version bump.

---

## Current Version: 1.2.0

Released: December 2024

### Features

- Multi-format support (YAML, JSON, TOML)
- Profile-based configuration overlays
- Recursive imports with cycle detection
- Deep merge with collision warnings
- Encrypted secrets with lazy decryption
- Complete provenance tracking
- CLI for configuration inspection
- pytest integration

### Recent Additions

- **TOML configuration format** — Use `.toml` files alongside YAML and JSON
- **`--format` CLI flag** — Explicitly specify input config format
- **Merge order fix** — Profile overlays now correctly have final say over imported values

---

## Phase 3: 1.3.x

**Focus: Hardening and Provenance Improvements**

### Planned

- **Source format metadata** — Record which format each value came from
- **Improved error clarity** — Better distinction between parse, merge, and secret errors
- **Cross-format merge documentation** — Document merge semantics across formats

### Potential Enhancements

- Programmatic access to value source information
- Enhanced debugging for complex import hierarchies

### Exclusions

- No public plugin stability guarantees
- No automatic plugin discovery

---

## Phase 4: 1.4.x (Optional)

**Focus: Experimental Parser Registration**

This phase depends on demonstrated user demand.

### Scope

- Public `register_parser()` API
- Experimental documentation with stability warnings
- Clear notice that parser APIs may change before 2.0

### When This Happens

- Users request custom format support
- Clear use cases emerge beyond YAML/JSON/TOML
- Community interest in extending SprigConfig

---

## Phase 5: 2.0.0

**Focus: Stable Parser Platform**

A 2.0 release happens only when public contracts must change.

### Scope

- Parser interfaces frozen and documented
- Supported plugin system with versioning guarantees
- Defined expectations for:
  - Parser lifecycle
  - Error behavior
  - Merge semantics

### Potential Enhancements

- Optional XML support
- Optional schema integration hooks
- Advanced provenance features

### What Triggers 2.0

- Need to change public APIs in breaking ways
- Parser plugin contracts require formalization
- Significant architectural changes

---

## What We're Not Planning

Some features are intentionally out of scope:

### Flat format support (INI, Properties)

Flat formats require inventing behavior (dot-splitting, type inference) that conflicts with SprigConfig's explicit philosophy. See [Philosophy](philosophy.md).

### Remote configuration

SprigConfig loads local files. Remote configuration (Consul, etcd, etc.) is a separate concern better handled by specialized tools.

### Hot reloading

Configuration is loaded once at startup. Hot reloading introduces complexity and potential race conditions.

### Schema validation

Use Pydantic or similar for validation after loading. SprigConfig focuses on loading and merging.

---

## Version History

### 1.2.0 (December 2024)

- TOML configuration format support
- `--format` CLI flag
- Merge order bug fix

### 1.1.0 (December 2024)

- Format-agnostic configuration loading
- JSON configuration format support
- Internal parser abstraction

### 1.0.0 (December 2024)

- Initial stable release
- YAML-based deep-merge configuration
- Profile overlays
- Recursive imports
- Secure lazy secrets
- CLI tooling

See [CHANGELOG](https://gitlab.com/dgw_software/sprig-config/-/blob/main/sprig-config-module/CHANGELOG.md) for complete version history.

---

## Contributing to the Roadmap

Have ideas for SprigConfig's future?

### Feature requests

Open an issue describing:
- The problem you're trying to solve
- Why existing features don't address it
- How the feature aligns with SprigConfig's principles

### Pull requests

- Discuss significant changes in an issue first
- Ensure backward compatibility
- Include tests for new behavior

See [CONTRIBUTING.md](https://gitlab.com/dgw_software/sprig-config/-/blob/main/sprig-config-module/CONTRIBUTING.md) for guidelines.

---

## Stability Promise

SprigConfig is committed to stability:

- **1.x releases** are backward compatible
- **Deprecation warnings** precede removal
- **Major versions** are infrequent and well-communicated
- **Migration guides** accompany breaking changes

You can depend on SprigConfig in production with confidence.

---

[← Back to Documentation](index.md)



---

# File: docs/security.md

---
layout: default
title: Security
---

# Security

SprigConfig provides secure handling of sensitive configuration values through encrypted secrets with lazy decryption. This guide covers key management, encryption workflow, and security best practices.

---

## Overview

SprigConfig uses **Fernet symmetric encryption** from the `cryptography` library. Sensitive values are stored as `ENC(...)` in configuration files and decrypted only when explicitly accessed.

Key security principles:
- **Encrypt at rest** — Secrets are encrypted in configuration files
- **Decrypt on demand** — Values stay encrypted until `.get()` is called
- **Redact by default** — Dumps and serialization hide secrets
- **Key separation** — Each environment has its own encryption key

---

## Encryption Format

Encrypted values use the `ENC()` wrapper:

```yaml
database:
  username: admin
  password: ENC(gAAAAABl_example_ciphertext_here...)

api:
  key: ENC(gAAAAABl_another_encrypted_value...)
```

SprigConfig automatically detects `ENC()` values and wraps them as `LazySecret` objects.

---

## Key Management

### Generating a key

Use the `cryptography` library to generate a Fernet key:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

Output looks like:
```
ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=
```

### One key per environment

Generate separate keys for each environment:

| Environment | Key Variable |
|-------------|--------------|
| Development | `DEV_SECRET_KEY` or shared `.env` |
| Test | `TEST_SECRET_KEY` or in-memory |
| Production | `APP_SECRET_KEY` via secret manager |

### Storing keys securely

**Never commit keys to version control.**

Store keys in:
- **Secret managers** — HashiCorp Vault, AWS Secrets Manager, Azure Key Vault
- **CI/CD protected variables** — GitLab CI/CD, GitHub Actions secrets
- **Local `.env` files** — Excluded from Git via `.gitignore`
- **Environment variables** — Set at deployment time

### Setting the key

SprigConfig provides multiple ways to configure the encryption key:

#### Option A: Environment variable

```bash
export APP_SECRET_KEY="your-fernet-key-here"
```

SprigConfig checks `APP_SECRET_KEY` automatically when decrypting.

#### Option B: Load from environment explicitly

```python
from sprigconfig.lazy_secret import ensure_key_from_env

# Loads APP_SECRET_KEY and validates it
ensure_key_from_env("APP_SECRET_KEY")
```

#### Option C: Set key directly

```python
from sprigconfig.lazy_secret import set_global_key

set_global_key("your-fernet-key-here")
```

#### Option D: Custom key provider

For key rotation or vault integration:

```python
from sprigconfig.lazy_secret import set_key_provider

def get_key_from_vault():
    # Fetch from secret manager
    return vault_client.get_secret("app-secret-key")

set_key_provider(get_key_from_vault)
```

### Key resolution order

When decrypting, SprigConfig checks for keys in this order:

1. Explicit key passed to `LazySecret`
2. Global key set via `set_global_key()`
3. Dynamic provider via `set_key_provider()`
4. Environment variable `APP_SECRET_KEY`

---

## Encrypting Values

Create a helper script for encrypting values:

```python
# encrypt_value.py
import os
import sys
from cryptography.fernet import Fernet

key = os.environ.get("APP_SECRET_KEY")
if not key:
    print("Set APP_SECRET_KEY first")
    sys.exit(1)

value = sys.argv[1]
f = Fernet(key.encode())
encrypted = f.encrypt(value.encode()).decode()
print(f"ENC({encrypted})")
```

Usage:

```bash
export APP_SECRET_KEY="your-key"
python encrypt_value.py "my-secret-password"
# Output: ENC(gAAAAABl...)
```

Then add to your configuration:

```yaml
database:
  password: ENC(gAAAAABl...)
```

---

## LazySecret Behavior

### Accessing secrets

Encrypted values become `LazySecret` objects:

```python
cfg = load_config(profile="prod")

# Returns LazySecret, not the plaintext
secret = cfg["database"]["password"]
print(type(secret))  # <class 'sprigconfig.lazy_secret.LazySecret'>

# Decrypt only when needed
plaintext = secret.get()
```

### Lazy decryption

Decryption happens only when `.get()` is called:
- Memory contains encrypted ciphertext until access
- Failed decryption raises `ConfigLoadError`
- Each `.get()` call decrypts (no caching of plaintext)

### Memory cleanup

For sensitive applications, use `.zeroize()` for best-effort memory cleanup:

```python
secret = cfg["database"]["password"]
password = secret.get()
# Use password...
secret.zeroize()  # Best-effort cleanup
```

Note: Python's garbage collection makes guaranteed memory cleanup impossible.

---

## Serialization and Redaction

### Default behavior: redacted

Secrets are redacted in dumps and serialization:

```python
cfg = load_config(profile="prod")

# Redacted output
print(cfg.to_dict())
# {'database': {'password': '<LazySecret>'}}

print(cfg.dump())
# database:
#   password: <LazySecret>
```

### Revealing secrets (unsafe)

For debugging, you can reveal secrets:

```python
# In code (unsafe!)
data = cfg.to_dict(reveal_secrets=True)
yaml_str = cfg.dump(safe=False)

# Via CLI (unsafe!)
sprigconfig dump --config-dir=config --profile=prod --secrets
```

**Warning:** Only use reveal options in secure, local environments. Never in logs or CI output.

---

## Key Rotation

### Rotation procedure

1. **Generate new key (K2):**
   ```python
   from cryptography.fernet import Fernet
   new_key = Fernet.generate_key().decode()
   ```

2. **Re-encrypt all secrets with K2:**
   ```python
   old_f = Fernet(old_key)
   new_f = Fernet(new_key)

   # For each secret
   plaintext = old_f.decrypt(old_ciphertext)
   new_ciphertext = new_f.encrypt(plaintext)
   ```

3. **Deploy updated configs + K2 together**

4. **Remove old key (K1) from all environments**

### Dual-key transition (optional)

Use a custom key provider for gradual rotation:

```python
def dual_key_provider():
    k1 = os.getenv("APP_SECRET_KEY_OLD")
    k2 = os.getenv("APP_SECRET_KEY")

    # Try new key first, fall back to old
    return k2 or k1

set_key_provider(dual_key_provider)
```

---

## CI/CD Security

### Pipeline best practices

```yaml
# GitLab CI example
deploy:
  script:
    - pip install sprig-config
    # Key is injected as protected variable
    - sprigconfig dump --config-dir=config --profile=prod  # Redacted
  variables:
    APP_SECRET_KEY: $PROD_SECRET_KEY  # Protected CI variable
```

### Security checklist

- [ ] `APP_SECRET_KEY` is a protected/masked CI variable
- [ ] Never echo or log secret keys
- [ ] Never use `--secrets` flag in CI logs
- [ ] Config dumps go to artifacts, not logs
- [ ] Different keys for each environment

---

## Error Handling

### Common errors

| Error | Cause |
|-------|-------|
| `No Fernet key available` | Key not set before accessing secret |
| `Invalid Fernet key` | Key is malformed or wrong length |
| `InvalidToken` | Wrong key or corrupted ciphertext |
| `ConfigLoadError` | Wraps cryptography errors |

### Handling decryption errors

```python
from sprigconfig import load_config, ConfigLoadError

try:
    cfg = load_config(profile="prod")
    password = cfg["database"]["password"].get()
except ConfigLoadError as e:
    if "Fernet key" in str(e):
        print("Missing or invalid encryption key")
    elif "InvalidToken" in str(e):
        print("Wrong key or corrupted secret")
    else:
        print(f"Config error: {e}")
```

---

## Security Audit Checklist

### Configuration files

- [ ] All sensitive values use `ENC()` wrapper
- [ ] No plaintext passwords in any environment
- [ ] No keys or tokens visible in files
- [ ] `.gitignore` excludes `.env` files

### Key management

- [ ] One key per environment
- [ ] Keys stored in secret manager or protected variables
- [ ] Keys rotated periodically
- [ ] Old keys removed after rotation

### Code practices

- [ ] Secrets accessed only when needed
- [ ] No logging of decrypted values
- [ ] `reveal_secrets` only used locally
- [ ] Key provider used for vault integration

### Verification commands

```bash
# Check for unencrypted sensitive values
grep -rn "password:" config/ | grep -v "ENC("
grep -rn "secret:" config/ | grep -v "ENC("
grep -rn "token:" config/ | grep -v "ENC("

# Verify all ENC values are present
grep -rn "ENC(" config/
```

---

## Best Practices Summary

1. **Encrypt everything sensitive** — Passwords, API keys, tokens
2. **Never commit keys** — Use secret managers or CI variables
3. **Use separate keys per environment** — Dev keys don't work in prod
4. **Decrypt only when needed** — Keep secrets lazy
5. **Redact by default** — Only reveal for debugging
6. **Rotate keys periodically** — At least annually
7. **Audit regularly** — Check for plaintext secrets

---

[← Back to Documentation](index.md)



---

# File: docs/snyk-gitlab-setup.md

# Snyk GitLab CI/CD Integration Setup

This guide walks you through integrating Snyk into your GitLab CI/CD pipeline.

---

## Prerequisites

- A Snyk account (free tier works fine)
- GitLab project with CI/CD enabled
- Admin or maintainer access to your GitLab project

---

## Step 1: Get Your Snyk API Token

1. Log in to [Snyk](https://app.snyk.io/)
2. Click your profile icon → **Account Settings**
3. Navigate to **API Token** section
4. Click **Click to show** to reveal your token
5. Copy the token (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

**Important**: Keep this token secure! It grants access to your Snyk account.

---

## Step 2: Add Snyk Token to GitLab CI/CD Variables

### Via GitLab UI:

1. Go to your GitLab project
2. Navigate to **Settings → CI/CD**
3. Expand **Variables** section
4. Click **Add variable**
5. Configure:
   - **Key**: `SNYK_TOKEN`
   - **Value**: Your Snyk API token (from Step 1)
   - **Type**: `Variable`
   - **Flags**:
     - ✅ **Protect variable** (recommended - only available on protected branches)
     - ✅ **Mask variable** (prevents token from appearing in job logs)
     - ❌ **Expand variable reference** (leave unchecked)
6. Click **Add variable**

### Optional: Add Snyk Organization ID

If you have multiple Snyk organizations:

1. In Snyk, go to **Settings → General**
2. Copy your **Organization ID**
3. Add another GitLab CI/CD variable:
   - **Key**: `SNYK_ORG`
   - **Value**: Your Snyk Organization ID
   - **Flags**: No special flags needed

---

## Step 3: Verify Integration

1. Push a commit to a branch or create a merge request
2. Go to **CI/CD → Pipelines**
3. Click the latest pipeline
4. In the **security** stage, you should see:
   - ✅ `bandit` - Python code security scan
   - ✅ `snyk_test` - Dependency vulnerability scan
   - ✅ `snyk_code` - Code security analysis (optional)
   - ✅ `sast` - GitLab SAST
   - ✅ `secret_detection` - GitLab secret detection

---

## Understanding the Jobs

### `bandit` Job
- **What**: Scans Python code for security issues
- **Checks**: Hardcoded passwords, SQL injection patterns, insecure crypto, etc.
- **Output**: `bandit-report.json` artifact

### `snyk_test` Job
- **What**: Scans dependencies (from `poetry.lock`) for known vulnerabilities
- **Checks**: CVEs in packages, license compliance
- **Output**: `snyk-report.json` artifact
- **Dashboard**: Results appear in your Snyk dashboard via `snyk monitor`

### `snyk_code` Job (Optional)
- **What**: Static code analysis for security vulnerabilities
- **Checks**: OWASP Top 10, CWE issues, data flow analysis
- **Output**: `snyk-code-report.json` artifact

---

## Severity Thresholds

Currently set to `--severity-threshold=high`:
- **Critical**: Always fails
- **High**: Fails the job
- **Medium**: Reported but doesn't fail
- **Low**: Reported but doesn't fail

To make it stricter (fail on medium+):
```yaml
- snyk test --severity-threshold=medium
```

To make it more permissive (critical only):
```yaml
- snyk test --severity-threshold=critical
```

---

## Making Snyk Required (Blocking)

Currently, Snyk jobs have `allow_failure: true` so they won't block your pipeline.

To make them required:

```yaml
snyk_test:
  # Remove or comment out this line:
  # allow_failure: true
```

**Recommendation**: Keep `allow_failure: true` initially, review results, fix critical issues, then remove it.

---

## Viewing Results

### In GitLab:
1. Go to pipeline → Click the job → View logs
2. Download artifacts → Open JSON reports

### In Snyk Dashboard:
1. Log in to [Snyk](https://app.snyk.io/)
2. Navigate to **Projects**
3. Find `sprig-config-module`
4. View detailed vulnerability reports, fix recommendations, and trends

---

## Snyk Free Tier Limits

- ✅ 200 tests/month
- ✅ Unlimited private repos
- ✅ Basic vulnerability database
- ✅ CLI and CI/CD integration

If you exceed limits, Snyk will still work but with degraded features.

---

## Troubleshooting

### "Authentication failed"
- Verify `SNYK_TOKEN` is set correctly in GitLab CI/CD variables
- Check token hasn't expired (Snyk tokens don't expire by default)

### "Organization not found"
- If using `SNYK_ORG`, verify the organization ID is correct
- Or remove the `--org=$SNYK_ORG` flag from `.gitlab-ci.yml`

### "Poetry lock file not found"
- Ensure `poetry.lock` is committed to your repository
- Snyk needs it to analyze exact dependency versions

---

## Best Practices

1. **Start Permissive**: Use `allow_failure: true` initially
2. **Review Weekly**: Check Snyk dashboard for new vulnerabilities
3. **Fix Incrementally**: Focus on Critical → High → Medium
4. **Keep Updated**: Run `poetry update` regularly to get security patches
5. **Monitor Trends**: Use Snyk dashboard to track security posture over time

---

## Next Steps

- [ ] Set up `SNYK_TOKEN` in GitLab CI/CD variables
- [ ] Push a commit to trigger the pipeline
- [ ] Review results in Snyk dashboard
- [ ] Fix any critical/high severity issues
- [ ] Consider enabling Snyk PR checks (requires Snyk GitHub/GitLab integration)
- [ ] Set up Slack/email notifications for new vulnerabilities

---

## Additional Resources

- [Snyk CLI Documentation](https://docs.snyk.io/snyk-cli)
- [Snyk GitLab Integration](https://docs.snyk.io/integrations/git-repository-scm-integrations/gitlab-integration)
- [Bandit Documentation](https://bandit.readthedocs.io/)



---

# File: sprig-config-module/CHANGELOG.md

# Changelog

All notable changes to **SprigConfig** will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [1.2.4] — 2025-12-21

### 🎯 Summary

This is a **backward-compatible feature completion release** that brings **TOML configuration support to full parity with YAML and JSON**.

TOML configs now support imports, profile overlays, and environment variable expansion with identical semantics across all supported formats.

---

### ✨ Added

* **Full TOML format support** with feature parity across:

  * Recursive imports
  * Profile overlays (`application-<profile>.toml`)
  * Environment variable expansion (`${VAR}` / `${VAR:default}`)
* Alias-aware extension handling (e.g. `yaml` / `yml`) during import resolution
* Comprehensive TOML-specific tests validating loader behavior and parity

---

### 🛠️ Fixed

* Import resolution edge cases where canonical extensions did not exist on disk (e.g. `.yaml` vs `.yml`)
* Incomplete TOML import and overlay handling uncovered during parity testing
* Ensured secrets are never persisted on long-lived objects during config loading

---

### 🔄 Changed

* Import resolution now deterministically falls back to format aliases when resolving files
* Internal loader logic hardened to treat **format and file extension as distinct concerns**
* Test coverage expanded to explicitly validate TOML behavior under real-world scenarios

---

### 🔒 Backward Compatibility

* No breaking changes
* No API changes
* No configuration changes required
* Existing YAML and JSON projects continue to work unchanged

---

### 🧭 Notes for Users

* TOML configuration files are now fully supported and behave identically to YAML and JSON
* Exactly **one configuration format may be used per run**
* Mixed-format imports remain intentionally unsupported

---

## [1.2.3] — 2025-12-20

### 🎯 Summary

This is a **documentation metadata synchronization release** to ensure PyPI correctly links to the hosted GitHub Pages documentation.

There are **no functional or behavioral changes**.

---

### 🔄 Changed

- Updated package metadata so PyPI points to the official documentation site hosted on GitHub Pages
- No code changes

---

### 🔒 Backward Compatibility

- No runtime changes
- No API changes
- No configuration changes
- Fully backward compatible

---

## [1.2.2] — 2025-12-20

### 🎯 Summary

This is a **packaging and documentation correction release** addressing issues discovered immediately after publishing 1.2.1.

There are **no functional or behavioral changes**.

---

### 🛠️ Fixed

- Corrected installation instructions to reference the proper package name (`sprig-config` instead of `sprigconfig`)
- Relaxed Python version requirement to allow installation on future Python 3.x releases (`>=3.13`)
- Regenerated lock file to reflect updated project metadata

---

### 🔄 Changed

- Documentation and packaging metadata adjustments finalized after 1.2.1 publication
- Release version incremented to comply with PyPI immutability rules

---

### 🔒 Backward Compatibility

- No runtime changes
- No API changes
- No configuration changes
- Fully backward compatible

---

### 🧭 Notes for Users

If you attempted to install **1.2.1** and encountered dependency or installation issues, upgrading to **1.2.2** resolves them. No other action is required.

---

## [1.2.1] — 2025-12-20

### 🎯 Summary

This is a **documentation and metadata release** that improves project discoverability and alignment across PyPI, GitHub, and hosted documentation.

There are **no functional or behavioral changes**.

---

### ✨ Added

- **PyPI project links** for Homepage and Documentation, pointing to the official GitHub Pages site
- Explicit Documentation URL surfaced on PyPI for easier navigation

---

### 🔄 Changed

- Updated package metadata to include `tool.poetry.urls`
- Improved consistency between PyPI, GitHub, and documentation site references

---

### 🔒 Backward Compatibility

- No runtime changes
- No API changes
- No configuration changes
- Fully backward compatible

---

### 🧭 Notes for Users

If you are upgrading from **1.2.0**, no action is required.  
This release exists to improve documentation visibility and packaging metadata only.

---

## [1.2.0] — 2025-12-20

### 🎯 Summary

This release adds **TOML configuration support** and fixes an important **merge order bug** that affected how profile overlays interact with imports.

---

### ✨ Added

- **TOML configuration format support** — use `.toml` files alongside YAML and JSON
- **`--format` CLI flag** — explicitly specify input config format (`yml`, `yaml`, `json`, `toml`)
- Security scanning in CI pipeline (Snyk, Bandit)

---

### 🛠️ Fixed

- **Merge order bug** — imports are now processed in the correct order:
  1. Base config (`application.<ext>`)
  2. Base imports
  3. Profile overlay (`application-<profile>.<ext>`)
  4. Profile imports

  Profile overlays now correctly have final say over imported values.

- Snyk CI job failures due to Docker entrypoint conflicts

---

### 🔄 Changed

- Test config files aligned across YAML, JSON, and TOML formats for stable generic tests
- Updated `config_loader.py` docstrings to document merge order

---

### 🔒 Backward Compatibility

- YAML remains the default configuration format
- Existing projects continue to work unchanged
- The merge order fix may change behavior if you relied on imports overriding profile values (which was unintended)

---

### 🚀 What's Next

- **1.3.x** — Provenance, debugging, and introspection improvements
- **2.0.0** — Stable parser and plugin contracts

See `ROADMAP.md` for full details.

---

## [1.1.0] — 2025-12-15

### 🎯 Summary

This release introduces **internal parser abstraction and format-agnostic configuration loading**, enabling future configuration formats while preserving **100% backward compatibility**.

There are **no breaking changes** and **no required user action**.

---

### ✨ Added

- Format-agnostic configuration loading architecture
- Built-in support for **JSON configuration files** alongside YAML
- Environment-selectable config format via `SPRIGCONFIG_FORMAT`
- Extension-aware config discovery (`application.<ext>`, `application-<profile>.<ext>`)
- Extension-aware import resolution across all config layers
- Internal parser delegation layer (foundation for future formats)
- Test tooling for safely capturing fully merged configuration dumps
- Improved consistency of metadata generation across formats

---

### 🔄 Changed

- `ConfigLoader` no longer parses YAML directly; parsing is delegated internally
- Configuration loading behavior is now **independent of file format**
- Import handling, deep-merge order, and metadata injection are consistent across YAML and JSON
- Test infrastructure updated to validate format parity without changing existing tests

---

### 🛠️ Fixed

- Import resolution edge cases when switching configuration formats
- Environment variable loading order affecting format selection in tests
- Minor loader bugs uncovered during JSON/YAML parity validation

---

### 🔒 Backward Compatibility

- YAML remains the default configuration format
- Existing YAML-based projects continue to work unchanged
- No public APIs were removed or altered
- Merge semantics, import behavior, and secret handling are unchanged

---

### 🧭 Notes for Users

- Exactly **one configuration format may be used per run**
- Mixed-format layering (e.g., YAML importing JSON) is intentionally not supported
- This release is primarily architectural, preparing the groundwork for future format extensibility

---

### 🚀 What’s Next

- **1.2.0** — Optional additional formats (e.g., TOML)
- **1.3.x** — Provenance, debugging, and introspection improvements
- **2.0.0** — Stable parser and plugin contracts

See `ROADMAP.md` for full details.

---

## [1.0.0] — 2025-12-02

### 🎉 Initial Stable Release

- YAML-based deep-merge configuration loader
- Profile overlays via `application-<profile>.yml`
- Recursive `imports:` with circular import detection
- Deterministic deep-merge semantics
- Secure lazy secret handling via `LazySecret`
- Rich metadata injection (`sprigconfig._meta`)
- CLI tooling for dumping resolved configuration

---

*This changelog is intentionally curated. Entries are added only for user-relevant or architecturally significant changes.*



---

# File: sprig-config-module/CONTRIBUTING.md

# Contributing to SprigConfig

Thank you for your interest in contributing to **SprigConfig**.

SprigConfig aims to provide **predictable, debuggable, Spring-style configuration composition for Python**, with a strong emphasis on clarity over cleverness.

Before opening an issue or pull request, please read the principles below.

---

## Guiding Principles

These principles are **non-negotiable** and guide all design decisions:

1. **Config behavior > file format**
2. **Parsing is a leaf concern**
3. **Backward compatibility is sacred in 1.x**
4. **2.0 only when contracts change**

If a change violates one of these, it is either deferred or requires a major version bump.

---

## Supported Configuration Formats

SprigConfig currently supports:

- **YAML**
- **JSON**

These formats were chosen because they **natively express hierarchical configuration**, which allows merge semantics to remain explicit and debuggable.

### About `.properties`, INI, and similar formats

Flat formats (e.g. `.properties`, `.ini`) do not natively express structure and require invented behavior such as:

- dot-splitting
- implicit hierarchy
- list coercion
- type inference rules

For this reason, these formats are **not supported by default**.

Support may be considered if:
- there is demonstrated real-world demand
- semantics are explicit and well-documented
- behavior does not silently alter merge or provenance rules

Forking or experimental extensions are encouraged if you wish to explore this space.

---

## Issues

When opening an issue, please include:

- What you expected to happen
- What actually happened
- Relevant config snippets (redacted if needed)
- Whether the issue affects backward compatibility

Feature requests should explain the **problem**, not just the solution.

---

## Pull Requests

Pull requests should:

- Preserve existing behavior unless explicitly discussed
- Include tests for new behavior
- Avoid introducing format-specific logic into merge or core loader paths
- Respect existing naming and structure conventions

Large changes should be discussed in an issue before implementation.

---

## Development Philosophy

SprigConfig favors:

- Explicit behavior over magic
- Deterministic merges over convenience
- Traceability over minimalism

If in doubt, choose the option that makes configuration behavior easier to **reason about at 3am during an outage**.

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.



---

# File: sprig-config-module/README.md

# 🌱 SprigConfig

[![Latest Version](https://gitlab.com/dgw_software/sprig-config/-/badges/release.svg)](https://gitlab.com/dgw_software/sprig-config/-/packages)

SprigConfig is a lightweight, opinionated configuration system for Python
applications. It provides layered YAML loading, profile overlays, environment
variable expansion, recursive imports, safe secret handling, and detailed metadata
tracking designed for clarity, reproducibility, and debuggability.

This updated README reflects the current, expanded architecture of SprigConfig —
including its test infrastructure, `.env` handling model, and secret‑management APIs.

---

# ⭐ Key Features

### ✔️ Profile Injection (Runtime-Driven)
Profiles are *never* taken from files. The active profile comes from:

1. `load_config(profile=...)`  
2. `APP_PROFILE`  
3. `pytest` → `"test"`  
4. Otherwise → `"dev"`

Injected into final config as:

```yaml
app:
  profile: <active>
```

If a YAML file contains `app.profile`, it is ignored with a warning.

---

### ✔️ Layered YAML Merging (Deep Merge)
SprigConfig merges:

1. `application.yml`
2. `application-<profile>.yml`
3. `imports: [file1.yml, file2.yml, …]`

Features include:

- Recursive dictionary merging  
- Override collision warnings  
- Partial merge clarity  
- Preservation of source metadata

---

### ✔️ Environment Variable Expansion
Patterns:

```
${VAR}
${VAR:default}
```

Expanded at load time. Missing variables fall back to defaults.

---

### ✔️ Secure Secret Handling
Values formatted as:

```
ENC(<ciphertext>)
```

are mapped to `LazySecret` objects.

- Decryption is lazy (on `.get()`)  
- Uses global Fernet key via `APP_SECRET_KEY`  
- Supports global key providers  
- Secrets redacted during dumps unless explicitly allowed  

---

### ✔️ Import Chains
Inside any YAML file:

```yaml
imports:
  - features.yml
  - security.yml
```

SprigConfig resolves imports relative to `APP_CONFIG_DIR` or the config root
and detects circular imports.

---

### ✔️ Metadata Injection
Every loaded config includes:

```
sprigconfig._meta:
  profile: <active>
  sources: [list of resolved files]
  import_trace: <graph of import relationships>
```

This helps debugging and auditing.

---

### ✔️ BOM-Safe YAML Reads
UTF‑8 with BOM (`utf-8-sig`) is automatically sanitized so Windows-created
files don’t introduce odd keys like `ï»¿server`.

---

# 📦 Installation

```bash
pip install sprig-config
# or
poetry add sprig-config
```

---

# 📁 Project Structure

```
sprigconfig/
    config_loader.py
    config.py
    lazy_secret.py
    deepmerge.py
    exceptions.py
    ...

docs/
    README_AI_Info.md
    (future docs go here)

tests/
    conftest.py
    conftest.md
    test_*.py
    test_*.md
    config/
```

### Documentation Strategy
- **docs/** → Project-wide documentation (AI disclosure, architecture notes)
- **tests/** → Each test module has matching `.md` explaining its purpose
- **conftest.md** → Documentation for the test framework itself  

This ensures the entire system is self-explaining.

---

# 📂 Configuration Layout Example

```
config/
  application.yml
  application-dev.yml
  application-test.yml
  application-prod.yml
  features.yml
  override.yml
```

### `application.yml`

```yaml
server:
  port: 8080
logging:
  level: INFO
```

### `application-dev.yml`

```yaml
server:
  port: 9090
imports:
  - features.yml
  - override.yml
```

### `override.yml`

```yaml
server:
  port: 9999
features:
  auth:
    methods: ["password", "oauth"]
```

---

# ⚙️ Runtime Selection & Profile Behavior

SprigConfig determines profile → merges → injects profile → processes imports.

```python
from sprigconfig import load_config

cfg = load_config(profile="dev")
print(cfg["server"]["port"])  # 9999
print(cfg["app"]["profile"])  # dev
```

---

# 🔐 Secret Handling with `LazySecret`

```yaml
secrets:
  db_user: ENC(gAAAAA...)
  db_pass: ENC(gAAAAA...)
```

```python
val = cfg["secrets"]["db_pass"]
assert isinstance(val, LazySecret)
print(val.get())  # plaintext
```

LazySecrets are:

- Safe by default  
- Not decrypted unless `.get()` is called  
- Redacted in dumps  

---

# 📜 `.env` Resolution Model

SprigConfig supports configuration directory override via:

1. `load_config(config_dir=...)`
2. `APP_CONFIG_DIR`
3. `.env` in the project root
4. Test overrides (`--env-path`)
5. Default: `./config`

### `.env` example:

```
APP_CONFIG_DIR=/opt/myapp/config
APP_SECRET_KEY=AbCdEf123...
```

---

# 🧪 Test Suite Overview

SprigConfig has a **documented, extensible test architecture**.

### Test categories:
- Config mechanics  
- Metadata & import tracing  
- Deep merge  
- Profile overlay behavior  
- LazySecret & crypto handling  
- CLI serialization tests  
- Integration tests with full directory copies  

### Documentation-per-test:
Every test module includes a paired `.md` file explaining its purpose and architecture.

---

# 🧰 Test CLI Flags (from `conftest.py`)

| Flag | Purpose |
|------|---------|
| `--env-path` | Use a custom `.env` file during tests |
| `--dump-config` | Print merged config for debugging |
| `--dump-config-format yaml|json` | Output format |
| `--dump-config-secrets` | Resolve LazySecrets |
| `--dump-config-no-redact` | Show plaintext secrets |
| `--debug-dump=file.yml` | Write merged config snapshot |
| `RUN_CRYPTO=true` | Enable crypto-heavy tests |

These make the test suite extremely reproducible and transparent.

---

# 🛡️ Production Guardrails

When profile = `prod`:

- Missing `logging.level` → default to `INFO`  
- `logging.level: DEBUG` blocked unless  
  ```
  allow_debug_in_prod: true
  ```
- Missing `application-prod.yml` → error  
- Missing `application-test.yml` (when test) → error  

---

# 🔗 Programmatic Access

```python
from pathlib import Path
from sprigconfig import ConfigLoader

loader = ConfigLoader(config_dir=Path("config"), profile="dev")
cfg = loader.load()

print(cfg.get("server.port"))
print(cfg.to_dict())
```

---

# 🧭 Migration Notes

- Remove `app.profile` from YAML files; runtime decides profile  
- Use imports for modularizing config trees  
- Secrets should always be stored as encrypted `ENC(...)` values  

---

## Versioning

SprigConfig follows [Semantic Versioning](https://semver.org/):

- **MAJOR** versions introduce breaking changes
- **MINOR** versions add backward-compatible functionality
- **PATCH** versions contain backward-compatible bug fixes

Pre-release versions (e.g. `-rc1`) indicate a release candidate.
They are feature-complete but may receive final fixes before a stable release
and are not recommended for production use unless explicitly intended for testing.

# 📚 Additional Documentation

Developer-focused documentation is available under the `docs/` directory:

- 📘 [Developer Guide](docs/README_Developer_Guide.md)
- 🧭 [Roadmap](ROADMAP.md)
- 📝 [Changelog](CHANGELOG.md)

These documents cover contributor workflows, test mechanics, Git usage,
CI/release processes, and internal design notes.

# 📄 License

MIT



---

# File: sprig-config-module/ROADMAP.md

# SprigConfig Roadmap (Parser Engine Focus)

## Guiding Principles

- Config behavior is more important than file format
- Parsing is treated as a leaf concern
- Backward compatibility is preserved throughout 1.x
- A 2.0 release occurs only when public contracts change

Any change that violates these principles is deferred or reserved for a 2.0 release.

---

## Phase 1 — 1.1.0 (Completed)

**Parser Abstraction (Internal, Backward Compatible)**

### Scope

- Internal `ConfigParser` abstraction introduced
- YAML parsing moved behind the abstraction
- Parser registry added (extension to parser)
- Loader delegates parsing instead of parsing directly
- All existing tests pass unchanged

### Non-Goals

- No public parser or plugin API
- No documentation for custom parsers
- No behavior changes
- No new defaults

---

## Phase 2 — 1.2.0

**Additional Formats**

### Scope

- Built-in JSON parser
- Built-in TOML parser (stdlib only)
- Explicit errors for unsupported file extensions
- Test coverage demonstrating mixed-format imports
- Documentation updated to reflect supported formats

### Compatibility

- YAML remains the default and recommended format
- No required configuration changes
- Merge, import, profile, and secret behavior unchanged

---

## Phase 3 — 1.3.x

**Hardening and Provenance Improvements**

### Scope

- Record source format metadata for loaded values
- Improve error clarity (parse vs merge vs secret resolution)
- Document merge semantics across formats

### Potential Enhancements

- Programmatic access to value source information

### Exclusions

- No public plugin stability guarantees
- No automatic plugin discovery

---

## Phase 4 — 1.4.x (Optional)

**Experimental Parser Registration**

### Scope

- Public `register_parser()` API
- Experimental documentation and warnings
- Explicit notice that parser APIs may change prior to 2.0

This phase is dependent on demonstrated user demand.

---

## Phase 5 — 2.0.0

**Stable Parser Platform**

### Scope

- Parser interfaces frozen and documented
- Supported plugin system with versioning guarantees
- Defined expectations for:
  - parser lifecycle
  - error behavior
  - merge semantics

### Potential Enhancements

- Optional XML support
- Optional schema integration hooks



---

# File: sprig-config-module/docs/AI_Info.md


# AI Assistance Disclosure for SprigConfig

This document provides transparency about how Artificial Intelligence (AI) tools
were used during the development of the **SprigConfig** project and its
associated test suite.

The goal of this disclosure is to clarify **what was AI-generated**,  
**what was human-authored**, and **how responsibility and verification were
handled** throughout development.

---

# 🤝 1. Nature of AI Involvement

AI tools (specifically ChatGPT) were used to:

- Accelerate boilerplate generation
- Provide test scaffolding ideas
- Suggest architectural patterns
- Draft documentation for fixtures, CLI options, and internal modules
- Assist with refactoring strategies
- Propose edge‑case scenarios for tests
- Improve readability or consistency across configuration utilities

**No code was accepted without human review.**  
All AI-generated content was tested, corrected, refined, or rewritten by the
project maintainer.

---

# 🧠 2. Human Ownership and Responsibility

Even where AI provided text or code, **the human developer is the sole author of
record** and maintains:

- Final architectural decisions  
- Code correctness  
- Security posture  
- Secret-handling practices  
- Licensing, governance, and maintainership  
- Test coverage guarantees  
- Technical accountability for the repository  

AI acted only as a drafting and ideation partner, not an autonomous developer.

---

# 🔍 3. Verification Practices

Every AI-assisted contribution was validated through:

- Manual code review  
- Unit and integration tests  
- Static analysis tools  
- Reasoned inspection of logic and edge cases  
- Comparison with established Python and DevOps best practices  

Where AI output was incorrect, inefficient, or insecure, it was corrected or replaced.

This ensures that only **verified, intentional, human-approved** code enters the repository.

---

# 🔒 4. Security and Sensitive Data

At no time were real secrets, credentials, or protected configuration materials
provided to AI systems.

Secret-handling mechanisms (e.g., `LazySecret`, Fernet encryption, environment-based
configuration) were designed, reviewed, and validated **outside of AI suggestions** to
ensure safe implementation.

---

# 🚦 5. Ethical Transparency

This disclosure is included to:

- Maintain honesty about the development process  
- Adhere to emerging best practices around AI co-authoring  
- Provide clarity to future maintainers and contributors  
- Document how automated tools were used within the project  

SprigConfig remains a **human‑driven project**, with AI assistance serving only to
improve productivity and documentation clarity.

---

# 📚 6. Guidance for Future Contributors

Contributors are welcome to use AI tools provided they:

1. **Verify all generated code**  
2. Follow project architecture and testing standards  
3. Avoid introducing sensitive material into AI prompts  
4. Document AI involvement when it materially shapes a commit  

Pull requests must still meet the same rigorous review standards regardless of
whether AI helped produce them.

---

# 🏁 7. Summary

AI helped with:

- Drafting text  
- Generating initial code skeletons  
- Suggesting improvements  
- Creating test documentation and READMEs  

Humans provided:

- Architectural direction  
- All testing and verification  
- Refactoring  
- Final approval of every commit  
- Security controls and design principles  

This ensures SprigConfig upholds high standards of quality, reliability, and
safety while benefiting from modern development tools.

---

If you have questions about AI involvement or maintainership practices, feel
free to open an issue or contact the repository owner.



---

# File: sprig-config-module/docs/GitLab.md


# SprigConfig GitLab CI Pipeline Documentation

This document explains the CI/CD pipeline defined in `.gitlab-ci.yml` for the **SprigConfig** project.
It covers the purpose of each job, how version-controlled publishing works, required authentication,
and how GitLab’s Package Registry integrates with Poetry-based publishing.

---

# 📌 Overview of the CI Pipeline

The CI pipeline is designed to:

- Perform linting and formatting checks
- Run unit tests with coverage
- Execute security scans (SAST + Secret Detection)
- Build and publish the SprigConfig package to GitLab’s internal PyPI registry
- Enforce strict version/tag consistency
- Require manual approval before publishing

The pipeline runs using `python:3.13-slim` and installs Poetry 2.2.x on each job.

---

# 🧱 Pipeline Structure

```
stages:
  - lint
  - test
  - security
  - deploy
```

Each stage corresponds to a logical phase of quality and deployment.

All jobs inherit from:

```
.default_setup:
  image: python:3.13-slim
  before_script:
    - cd sprig-config-module
    - pip install poetry==2.2.0
    - poetry install
```

This ensures consistent tooling across jobs.

---

# 🔎 Workflow Rules

The pipeline runs on:

- **Any commit to any branch**
- **Any tag pushed to the repository**

Manual deploy jobs run **only on version tags** (`v1.2.0`, `V0.1.9`, etc.).

---

# 🧹 Lint Stage

Job: `lint`

Purpose: Verify style and best practices using Ruff.

```
poetry run ruff check src
```

Artifacts include `ruff.log` for offline review.

---

# 🧪 Test Stage

Job: `pytest`

Features:

- Runs full unit test suite
- Coverage via `pytest-cov`
- Injects a known test Fernet key (`APP_SECRET_KEY`) for `LazySecret` tests
- Produces coverage + JUnit reports for GitLab UI

Artifacts include:

- `coverage.xml`
- JUnit test reports
- Logs from tests

---

# 🔒 Security Stage

Two GitLab-provided scanners run automatically:

- **SAST** (Static Application Security Testing)
- **Secret Detection**

These use GitLab’s security templates and require no additional configuration.

---

# 🚀 Deploy Stage (Manual)

There are **two deployment jobs**, both manual:

---

## 1️⃣ `dry_run_pypi`

Purpose:

- Ensures the project can *build* successfully
- Ensures version tags match `pyproject.toml`
- Performs a `poetry publish --dry-run`
- Does **not** upload the package

Version check logic:

```
pyproject version = poetry version -s
tag version = CI_COMMIT_TAG (stripped of v/V)
```

If they differ → job fails.

Artifacts include the `dist/` directory.

---

## 2️⃣ `deploy_pypi`

Runs only after:

- `dry_run_pypi` succeeded
- Manual approval is given

This job performs the actual publish:

```
poetry publish --no-interaction -r gitlab-pypi
```

This uploads the wheel + sdist to the GitLab Package Registry.

---

# 🔑 Authentication Requirements

The CI pipeline uses environment variables:

```
GITLAB_PYPI_TOKEN    # must have write_registry scope
POETRY_HTTP_BASIC_GITLAB_PYPI_USERNAME="__token__"
POETRY_HTTP_BASIC_GITLAB_PYPI_PASSWORD=$GITLAB_PYPI_TOKEN
```

This is the official pattern for authenticated PyPI publishing.

---

# 🏷️ Tagging Rules (Strict)

A tag triggers the deploy pipeline **only if**:

- It starts with `v` or `V`
- It matches `pyproject.toml` version (after removing leading v/V)
- It is pushed to GitLab

Examples:

| Tag pushed | pyproject version | Allowed? | Reason |
|-----------|-------------------|----------|--------|
| `v1.2.0` | `1.2.0` | ✔️ | Correct |
| `V2.0.1` | `2.0.1` | ✔️ | Correct |
| `1.0.0` | `1.0.0` | ❌ | Must start with v/V |
| `v1.1` | `1.1.5` | ❌ | Version mismatch |

---

# 📦 Package Registry Information

The registry URL appears in `pyproject.toml`:

```
[[tool.poetry.source]]
name = "gitlab-pypi"
url = "https://gitlab.tsod.ad.usmc.mil/api/v4/projects/<project-id>/packages/pypi"
priority = "supplemental"
```

Poetry uses this when running:

```
poetry publish -r gitlab-pypi
```

---

# 🧭 Summary

The SprigConfig CI pipeline guarantees:

- Consistent Python + Poetry environment
- Automatic linting, testing, and scanning
- Strict version consistency between tags and published builds
- Safety through dry-run publishing
- Manual confirmation before releasing
- Secure deployment using GitLab's registry and tokens

This ensures that all published versions are safe, validated, and traceable.




---

# File: sprig-config-module/docs/PyPI.md


# SprigConfig Packaging & GitLab PyPI Publishing

This document explains how SprigConfig is packaged, versioned, and published to the
GitLab Package Registry using Poetry and GitLab CI pipelines.

---

# 📦 Packaging Overview

SprigConfig uses **Poetry 2.2.x** as its build and dependency manager.

Running:

```
poetry build
```

creates:

```
dist/
  sprigconfig-<version>.tar.gz
  sprigconfig-<version>-py3-none-any.whl
```

This is reproducible thanks to deterministic builds and pinned dependencies.

---

# 🏗️ Local Build Instructions

To build locally:

```
cd sprig-config-module
poetry install
poetry build
```

No additional steps are required. Poetry handles building:

- Wheel  
- Source distribution (sdist)  

---

# 🔑 Authentication for Publishing

Publishing requires:

- A GitLab **project** or **group token**
- Token must have: `write_registry`

Environment variables:

```
POETRY_HTTP_BASIC_GITLAB_PYPI_USERNAME="__token__"
POETRY_HTTP_BASIC_GITLAB_PYPI_PASSWORD="$GITLAB_PYPI_TOKEN"
```

These instruct Poetry how to authenticate to GitLab’s registry.

You can test auth locally:

```
poetry publish --dry-run -r gitlab-pypi
```

---

# 🧭 Registry Configuration in pyproject.toml

```
[[tool.poetry.source]]
name = "gitlab-pypi"
url = "https://gitlab.tsod.ad.usmc.mil/api/v4/projects/<project-id>/packages/pypi"
priority = "supplemental"
```

Details:

- PyPI.org remains the primary source  
- GitLab registry is supplemental  
- Builds publish *only* to GitLab registry  

---

# 🏷️ Versioning Workflow

Version is set using:

```
poetry version patch
poetry version minor
poetry version major
```

Or manually:

```
poetry version 1.5.2
```

This updates:

- `pyproject.toml`
- internal version metadata

Git tags must match these versions.

---

# 🚀 Publishing Workflow (via CI)

Publishing is performed only by GitLab CI, not manually.

### 1️⃣ Developer pushes a version tag

```
git tag v1.2.0
git push --tags
```

### 2️⃣ CI runs `dry_run_pypi`

- Ensures tag matches version  
- Builds the package  
- Runs a simulated publish  

### 3️⃣ CI runs `deploy_pypi` (manual approval)

- Performs a real `poetry publish`  
- Uploads artifacts to GitLab’s registry  

This ensures:

- Reproducible publishing  
- No accidental uploads  
- Manual human approval  

---

# 📥 Consuming SprigConfig from GitLab PyPI

Add this to the consumer project's `pyproject.toml`:

```
[[tool.poetry.source]]
name = "sprigconfig-internal"
url = "https://gitlab.tsod.ad.usmc.mil/api/v4/projects/<project-id>/packages/pypi"
priority = "supplemental"
```

Then:

```
poetry add sprig-config
```

---

# 🧪 Troubleshooting

### ❌ 401 Unauthorized  
Token missing or lacking `write_registry`.

### ❌ version mismatch  
Tag does not match Poetry version.

### ❌ registry not found  
Incorrect project ID in source URL.

### ❌ failed to build  
Re-run locally:

```
poetry build -vvv
```

---

# ✔️ Summary

SprigConfig’s packaging is:

- Poetry-driven  
- Deterministic  
- Enforced by CI  
- Safe (dry-run first)  
- Published only on valid version tags  
- Hosted entirely in GitLab’s internal registry  

This makes SprigConfig easy to distribute, version, and integrate into other systems across the organization.



---

# File: sprig-config-module/docs/README_Developer_Guide.md

# SprigConfig – Developer Guide

This guide is intended for developers working on SprigConfig itself.
It covers repository structure, test behavior, Git workflows, CI/release
processes, and internal design notes.

## Getting Started
- Local development setup
- Running tests

## Repository Notes
- [Test config files & git skip-worktree](git_skip_worktree_for_test_config_files.md)

## Release & CI
- [Release checklist](release_checklist.md)
- [GitLab notes](GitLab.md)
- [PyPI publishing](PyPI.md)



---

# File: sprig-config-module/docs/SprigConfig_ENC_BestPractices.md

# SprigConfig — Secrets & `ENC(...)` Best Practices  
**Updated for the global‑key API, enhanced LazySecret behavior, and secure dump rules**

SprigConfig supports encrypted configuration values using `ENC(...)` wrappers combined with a centrally managed Fernet key. This document explains key generation, encryption workflow, runtime usage, and operational security guidance.

---

## 1. Key Material

SprigConfig uses **Fernet keys** from the `cryptography` package.

### Generate a key

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### Storage & handling
- Create **one Fernet key per environment** (dev, test, stage, prod).
- Never commit keys into source control.
- Store only in:
  - Secret managers (Vault, AWS SM, GitLab Protected CI variables, etc.)
  - Local `.env` files **excluded from Git**
  - Encrypted credential stores
- Keys are **never** stored in YAML.

---

## 2. SprigConfig Global-Key API (New)

You must configure the Fernet key **before** loading encrypted configs.

### Option A — Load directly from environment

```python
from sprigconfig.lazy_secret import ensure_key_from_env
ensure_key_from_env("APP_SECRET_KEY")
```

### Option B — Set the key directly

```python
from sprigconfig.lazy_secret import set_global_key
set_global_key("<base64-fernet-key>")
```

### Option C — Provide a custom key provider

Useful for rotations or retrieving keys from a vault:

```python
from sprigconfig.lazy_secret import set_key_provider

def retrieve_key():
    return os.getenv("APP_SECRET_KEY")

set_key_provider(retrieve_key)
```

The key is validated immediately and raises `ConfigLoadError` if invalid.

---

## 3. Encrypting Values

Create a helper script that reads the Fernet key and outputs encrypted strings:

```bash
export APP_SECRET_KEY="<key>"
python encrypt_value.py "superSecret"
```

Write encrypted values in YAML as:

```yaml
db:
  password: ENC(gAAAAABcExampleCiphertextHere)
```

SprigConfig automatically detects and wraps these as `LazySecret` objects.

---

## 4. Runtime Behavior of LazySecret (Updated)

Encrypted fields become `LazySecret` instances.

### Access plaintext explicitly

```python
pwd = cfg["db"]["password"].get()
```

Important characteristics:

- Decryption happens **only on demand**.
- Values remain encrypted in memory until `.get()` is called.
- Never log decrypted values.
- Avoid storing decrypted values in long-lived structures.

### Serialization rules

- `Config.to_dict()` **redacts** all secrets by default.
- `Config.to_dict(reveal_secrets=True)` returns plaintext — **unsafe**, use only for debugging.
- YAML dumps via `.dump()` follow the same redaction rules.

---

## 5. Processing Order

SprigConfig processes configuration in this sequence:

1. Load `application.yml`
2. Load `application-<profile>.yml`
3. Apply overlays and **deep merge**
4. Resolve recursive imports and detect cycles
5. Apply `${ENV}` expansions
6. Wrap `ENC(...)` values as `LazySecret`

This ensures encryption refers to the final resolved value.

---

## 6. Key Rotation

Recommended approach:

1. Generate new key **K2**.
2. Re-encrypt all secrets with **K2**.
3. Deploy updated configs + K2 simultaneously.
4. Remove old key **K1** from all environments.

### Optional dual‑key mode
Using a custom key provider, you may temporarily support:

- Decrypt with K1 or K2  
- Re-encrypt exclusively with K2  

This permits staggered rollouts.

---

## 7. CI/CD & Local Development

### CI/CD pipelines

- Inject `APP_SECRET_KEY` via secure CI variables.
- Do not echo secrets or decrypted values.
- Disable reveal mode except in manual debugging jobs.
- Avoid printing full config dumps unless redacted.

### Local development

- Use a `.env` file that is **git‑ignored**.
- Use `python‑dotenv` if convenient.
- Regenerate dev keys freely—dev secrets should never be production-realistic.

---

## 8. CLI Dump Behavior (New)

SprigConfig's CLI supports safe debugging.

### Redacted dump (default)

```bash
sprigconfig dump config/
```

### Reveal dump (unsafe—plaintext)

```bash
sprigconfig dump --reveal config/
```

Always avoid `--reveal` in shared logs or CI.

---

## 9. Auditing & Quality Checks

Regularly verify:

- All sensitive fields use `ENC(...)`
- `APP_SECRET_KEY` is present in each environment
- No plaintext passwords appear in commit history  
- Imports and overlays do not accidentally introduce unencrypted secrets

Tools:

```bash
grep -R "ENC(" -n config/
grep -R "password:" -n config/
```

---

## 10. Failure Modes & Errors

- Missing key → `ConfigLoadError("No Fernet key available …")`
- Invalid key → immediate validation error in `set_global_key`
- Corrupted ciphertext → `InvalidToken` wrapped as `ConfigLoadError`
- Attempting to decrypt without configured key → `ConfigLoadError`

---

## 11. Summary

SprigConfig’s secret-handling philosophy:

- **Encrypt everything sensitive at rest**
- **Never commit keys**
- **Load keys only from trusted sources**
- **Decrypt only when explicitly needed**
- **Redact by default**
- **Support clean rotation**

This ensures your configuration system remains secure, predictable, and maintainable across all environments.

---

If you need an additional version of this document (PDF, DOCX, GitLab‑formatted README, or an example encryption helper), I can generate it anytime.



---

# File: sprig-config-module/docs/building_documentation.md

# Building SprigConfig Documentation

This guide explains how to build and preview the SprigConfig documentation locally.

## Prerequisites

The documentation is built using [MkDocs](https://www.mkdocs.org/) with the Material theme and mkdocstrings plugin for API reference generation.

### Install Documentation Dependencies

From the `sprig-config-module/` directory:

```bash
# Install documentation dependencies
poetry install --with docs

# Or if already installed, update
poetry update --with docs
```

This installs:
- `mkdocs` - Documentation site generator
- `mkdocs-material` - Material theme
- `mkdocstrings[python]` - Automatic API reference from docstrings
- `mkdocs-git-revision-date-localized-plugin` - Git-based page dates

## Building the Documentation

### Serve Locally (Development)

To build and serve the documentation with live reload:

```bash
cd sprig-config-module
poetry run mkdocs serve
```

This will:
1. Build the documentation
2. Start a local server at http://127.0.0.1:8000
3. Watch for file changes and auto-reload

**Access the docs:** Open http://127.0.0.1:8000 in your browser

### Build Static Site

To build the static HTML site:

```bash
cd sprig-config-module
poetry run mkdocs build
```

Output will be in `sprig-config-module/site/`

### Build with Custom Port

```bash
poetry run mkdocs serve --dev-addr=127.0.0.1:8080
```

## Documentation Structure

```
docs/                           # User-facing documentation (GitHub Pages)
├── index.md                    # Home page
├── getting-started.md          # Installation & quickstart
├── configuration.md            # Configuration guide
├── profiles.md                 # Profiles documentation
├── imports.md                  # Imports guide
├── merge-order.md              # Merge semantics
├── security.md                 # Security & secrets
├── cli.md                      # Command-line interface
├── faq.md                      # FAQ
├── philosophy.md               # Design philosophy
├── roadmap.md                  # Future plans
└── api/                        # API Reference (auto-generated)
    ├── index.md                # API overview
    ├── core.md                 # Core API (load_config, Config, ConfigLoader)
    ├── secrets.md              # LazySecret API
    ├── utilities.md            # deep_merge, ConfigSingleton
    └── exceptions.md           # Error handling

sprig-config-module/docs/       # Developer guides (internal)
├── README_Developer_Guide.md   # Developer overview
├── release_checklist.md        # Release process
├── migration_guide.md          # Version migration guide
├── SprigConfig_ENC_BestPractices.md  # Secret best practices
├── GitLab.md                   # GitLab CI/CD
├── PyPI.md                     # PyPI publishing
└── ...
```

## Configuration

Documentation configuration is in `sprig-config-module/mkdocs.yml`:

```yaml
site_name: SprigConfig Documentation
theme:
  name: material
  palette:
    primary: green
    accent: light green

plugins:
  - search
  - mkdocstrings      # Auto-generate API docs from docstrings
  - git-revision-date-localized

nav:
  - Home: ../docs/index.md
  - Getting Started: ...
  - API Reference: ...
```

## API Reference Generation

API documentation is automatically generated from Python docstrings using mkdocstrings.

### How It Works

1. **Docstrings in source code:**
   ```python
   # src/sprigconfig/config.py
   class Config:
       """Dict-like configuration wrapper with dotted-key access.

       Args:
           data: Configuration data as nested dict
           meta: Optional metadata dict

       Example:
           >>> cfg = Config({"app": {"name": "MyApp"}})
           >>> cfg.get("app.name")
           'MyApp'
       """
   ```

2. **Reference in markdown:**
   ```markdown
   # docs/api/core.md
   ## Config

   ::: sprigconfig.Config
   ```

3. **Generated output:**
   MkDocs automatically extracts docstrings and generates formatted API documentation

### Supported Docstring Styles

SprigConfig uses **Google-style** docstrings:

```python
def load_config(profile: str, config_dir: Path = None) -> Config:
    """Load configuration with the specified profile.

    Args:
        profile: Profile name (e.g., 'dev', 'test', 'prod')
        config_dir: Optional config directory path

    Returns:
        Loaded configuration as Config object

    Raises:
        ConfigLoadError: If configuration cannot be loaded

    Example:
        >>> cfg = load_config(profile="dev")
        >>> cfg.get("app.name")
        'MyApp'
    """
```

## Previewing Changes

### Local Preview Workflow

1. Make changes to documentation files
2. Save the file
3. MkDocs auto-reloads in browser
4. Review changes
5. Iterate

### Testing Broken Links

```bash
# Build and check for broken links
poetry run mkdocs build --strict

# This will fail if there are:
# - Broken internal links
# - Missing navigation entries
# - Invalid markdown syntax
```

## Deploying Documentation

### GitHub Pages (Automated)

Documentation is automatically deployed to GitHub Pages on push to `main`:

```bash
# Manual deployment (if needed)
poetry run mkdocs gh-deploy
```

This will:
1. Build the documentation
2. Push to `gh-pages` branch
3. Trigger GitHub Pages deployment

### GitLab Pages

For GitLab Pages, add to `.gitlab-ci.yml`:

```yaml
pages:
  stage: deploy
  script:
    - cd sprig-config-module
    - poetry install --with docs
    - poetry run mkdocs build --site-dir ../public
  artifacts:
    paths:
      - public
  only:
    - main
```

## Customizing the Documentation

### Add a New Page

1. Create markdown file in `docs/`:
   ```bash
   touch docs/my-new-page.md
   ```

2. Add to navigation in `mkdocs.yml`:
   ```yaml
   nav:
     - My New Page: ../docs/my-new-page.md
   ```

3. Write content using markdown

### Add API Documentation

To document a new module:

1. Ensure module has docstrings:
   ```python
   # src/sprigconfig/my_module.py
   class MyClass:
       """My class description."""
       pass
   ```

2. Create API reference page:
   ```markdown
   # docs/api/my-module.md
   ## MyClass

   ::: sprigconfig.my_module.MyClass
   ```

3. Add to navigation:
   ```yaml
   nav:
     - API Reference:
         - My Module: ../docs/api/my-module.md
   ```

## Troubleshooting

### Issue: "No module named 'sprigconfig'"

**Solution:** Ensure you're running from `sprig-config-module/` directory where `src/` is located.

### Issue: Mkdocstrings can't find module

**Solution:** Check `paths` in mkdocs.yml:

```yaml
plugins:
  - mkdocstrings:
      handlers:
        python:
          paths: [src]  # Must point to source directory
```

### Issue: Live reload not working

**Solution:**
- Check firewall settings
- Try different port: `mkdocs serve --dev-addr=127.0.0.1:8080`
- Clear browser cache

### Issue: Broken links in navigation

**Solution:** Use relative paths from `mkdocs.yml` location:

```yaml
nav:
  - Home: ../docs/index.md           # Correct (relative to mkdocs.yml)
  - API: ../docs/api/core.md         # Correct
```

## Best Practices

1. **Write docstrings first** - Document code as you write it
2. **Use examples** - Include code examples in docstrings
3. **Test locally** - Always preview before committing
4. **Check links** - Run `mkdocs build --strict` before deploying
5. **Keep it organized** - Follow existing structure and patterns
6. **Update navigation** - Add new pages to `mkdocs.yml`

## Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [mkdocstrings](https://mkdocstrings.github.io/)
- [Google-style Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)



---

# File: sprig-config-module/docs/git_skip_worktree_for_test_config_files.md

# Handling Test Config Files with Git (skip-worktree)

This repository contains **test configuration files that are intentionally modified during test runs**.

To prevent these changes from being accidentally staged or committed, we use Git’s **`skip-worktree`** mechanism.

This document explains *why* this is needed and *how* to work with it safely.

---

## Why This Exists

Some files under:

```
tests/config/
```

are mutated as part of automated tests (for example, secrets injection, write-back behavior, or runtime normalization).

These changes are:
- Expected
- Local-only
- Not meaningful to commit

However, the files **must remain tracked** by Git so tests have a known starting state.

`skip-worktree` solves this exact problem.

---

## What `skip-worktree` Does

When a file is marked with `skip-worktree`:

- ✅ The file remains **tracked** by Git
- ✅ Local modifications are **ignored by `git status`**
- ✅ `git add .` will **not stage the file**
- ✅ You can still explicitly stage the file when you *intend* to commit changes

This is **not the same** as `.gitignore` and is safe for this use case.

---

## Marking a File as skip-worktree

From the repository root:

```bash
git update-index --skip-worktree tests/config/application-secrets.yml
```

You may apply this to multiple files:

```bash
git update-index --skip-worktree tests/config/*.yml
```

After this, `git status` should no longer show changes for those files.

---

## Intentionally Committing a Change

If you *do* want to commit an update to one of these files:

```bash
git update-index --no-skip-worktree tests/config/application-secrets.yml
git add tests/config/application-secrets.yml
```

After committing, it is recommended to re-apply `skip-worktree`:

```bash
git update-index --skip-worktree tests/config/application-secrets.yml
```

This makes intent explicit and avoids accidental commits later.

---

## Do NOT Use `assume-unchanged`

You may see advice online suggesting:

```bash
git update-index --assume-unchanged <file>
```

**Do not use this here.**

Reasons:
- It is intended as a *performance hint*, not a workflow tool
- Git may silently re-detect changes
- Behavior is unreliable across merges and rebases

For intentional local divergence, **`skip-worktree` is the correct choice**.

---

## Notes

- `skip-worktree` is **local-only** and does not affect other developers
- Each developer must apply it on their own machine
- CI environments should **not** use `skip-worktree`

---

## Summary

Use `skip-worktree` when:
- Files must be tracked
- Tests legitimately modify them
- Changes should not be committed accidentally

This repository intentionally uses that pattern for certain test config files.




---

# File: sprig-config-module/docs/migration_guide.md

# SprigConfig Migration Guide

This guide helps you upgrade SprigConfig across versions. SprigConfig follows [Semantic Versioning](https://semver.org/), so:

- **MAJOR** versions (e.g., 1.x → 2.x) may introduce breaking changes
- **MINOR** versions (e.g., 1.1 → 1.2) add features while maintaining backward compatibility
- **PATCH** versions (e.g., 1.2.3 → 1.2.4) contain only bug fixes and are always safe to upgrade

## Quick Version Check

```bash
# Check your current version
python -c "import sprigconfig; print(sprigconfig.__version__)"

# Or via pip
pip show sprigconfig | grep Version
```

## Current Version: 1.2.4

All 1.x releases are backward compatible. You can safely upgrade from any 1.x version to 1.2.4.

---

## Upgrading to 1.2.x (TOML Support)

**From:** 1.0.x, 1.1.x
**To:** 1.2.0+
**Risk:** Low
**Breaking Changes:** None

### What's New

- **TOML configuration format support** (in addition to YAML and JSON)
- **CLI `--format` flag** for explicit format selection
- **Merge order fix** for imports and profile overlays

### Installation

```bash
pip install --upgrade sprigconfig
```

### Migration Steps

#### 1. No Action Required

If you're using YAML or JSON configurations, **no changes are needed**. Your existing configuration will continue to work exactly as before.

#### 2. Optional: Adopt TOML

If you want to use TOML instead of YAML:

**Before (YAML):**
```yaml
# config/application.yml
database:
  host: localhost
  port: 5432
```

**After (TOML):**
```toml
# config/application.toml
[database]
host = "localhost"
port = 5432
```

**Important:** Use **exactly one format** per project. Mixed-format imports are not supported.

#### 3. Review Merge Order Behavior

Version 1.2.0 fixed a merge order bug. If you were relying on imports to override profile values (which was unintended behavior), you may see different results.

**Correct merge order (1.2.0+):**
1. Base config (`application.yml`)
2. Base imports
3. Profile overlay (`application-<profile>.yml`)
4. Profile imports

**Profile overlays now have final say**, which is the intended behavior.

**Action:** Test your configuration merging in a dev environment before deploying to production.

### Testing Your Migration

```bash
# Verify configuration loads correctly
sprigconfig dump --profile dev

# Check merge order
sprigconfig dump --profile prod --show-provenance
```

---

## Upgrading to 1.1.x (JSON Support)

**From:** 1.0.x
**To:** 1.1.0+
**Risk:** Very Low
**Breaking Changes:** None

### What's New

- **JSON configuration format support** (in addition to YAML)
- Format-agnostic configuration loading
- Extension-aware config discovery
- Internal parser abstraction

### Installation

```bash
pip install --upgrade sprigconfig
```

### Migration Steps

#### 1. No Action Required

YAML configurations continue to work without any changes.

#### 2. Optional: Use JSON

If you prefer JSON format:

**Before (YAML):**
```yaml
# config/application.yml
app:
  name: MyApp
  debug: true
```

**After (JSON):**
```json
// config/application.json
{
  "app": {
    "name": "MyApp",
    "debug": true
  }
}
```

#### 3. Environment Variable Changes (Optional)

If you were using undocumented environment variables for format selection, use the new standard:

```bash
# Old (undocumented, may not work)
CONFIG_FORMAT=json

# New (official)
SPRIGCONFIG_FORMAT=json
```

### Testing Your Migration

```bash
# Verify YAML still works
sprigconfig dump --profile dev

# Or try JSON
sprigconfig dump --profile dev --format json
```

---

## Upgrading from Pre-1.0

If you're upgrading from a pre-release or development version, please review the [1.0.0 release notes](../CHANGELOG.md#100--2025-12-02) carefully for breaking changes and migration requirements.

---

## Common Migration Scenarios

### Scenario 1: Simple YAML Configuration

**Question:** I only use basic YAML files. Do I need to change anything?

**Answer:** No. All 1.x versions are fully backward compatible with basic YAML configurations.

### Scenario 2: Using Encrypted Secrets

**Question:** Will my encrypted secrets still work?

**Answer:** Yes. Secret handling is unchanged across all 1.x versions. Your `ENC()` values will continue to work exactly as before.

### Scenario 3: Multiple Environments (Profiles)

**Question:** I use dev, test, and prod profiles. Will they work?

**Answer:** Yes. Profile handling is unchanged, though the merge order fix in 1.2.0 ensures profile overlays correctly override imported values (as intended).

### Scenario 4: Recursive Imports

**Question:** I have complex import chains. Will they break?

**Answer:** No. Import handling is backward compatible. The 1.2.0 merge order fix actually makes imports work more correctly.

---

## Deprecation Policy

SprigConfig follows these deprecation principles:

1. **No surprise removals** - Features are deprecated for at least one MINOR version before removal
2. **Clear warnings** - Deprecated features log warnings when used
3. **Migration path** - Alternatives are provided before deprecation
4. **Semantic versioning** - Breaking changes only occur in MAJOR versions

### Currently Deprecated

**None.** All features in SprigConfig 1.x are actively supported.

---

## Python Version Compatibility

| SprigConfig Version | Python Versions | Notes |
|---------------------|-----------------|-------|
| 1.2.4 (current)     | 3.13+          | Strict requirement |
| 1.2.0 - 1.2.3       | 3.13+          | Strict requirement |
| 1.1.0               | 3.13+          | Strict requirement |
| 1.0.0               | 3.13+          | Strict requirement |

**Note:** SprigConfig requires Python 3.13 or newer. Earlier Python versions are not supported.

---

## Troubleshooting Upgrades

### Issue: Configuration not loading after upgrade

**Symptoms:**
- `ConfigLoadError` exceptions
- Missing configuration values
- Unexpected merge results

**Solutions:**

1. **Verify your SprigConfig version:**
   ```bash
   pip show sprigconfig
   ```

2. **Check configuration file syntax:**
   ```bash
   # For YAML
   python -c "import yaml; yaml.safe_load(open('config/application.yml'))"

   # For JSON
   python -c "import json; json.load(open('config/application.json'))"
   ```

3. **Dump configuration to see what's loaded:**
   ```bash
   sprigconfig dump --profile dev
   ```

4. **Enable debug logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)

   from sprigconfig import load_config
   cfg = load_config()
   ```

### Issue: Merge order changed in 1.2.0

**Symptoms:**
- Profile values are different than expected
- Imports seem to override profile settings

**Solution:**

This is the intended behavior fix. Profile overlays should have final say.

**Before (incorrect, pre-1.2.0):**
```
1. Base config
2. Base imports (could override base)
3. Profile overlay
4. Profile imports (could override profile!) ← Bug
```

**After (correct, 1.2.0+):**
```
1. Base config
2. Base imports
3. Profile overlay (overrides everything above)
4. Profile imports (extends profile)
```

If you were relying on the old behavior, move values from imports to profile overlays.

### Issue: Secrets not decrypting

**Symptoms:**
- `LazySecret` objects not decrypting
- "Invalid token" or decryption errors

**Solutions:**

1. **Verify `APP_SECRET_KEY` is set:**
   ```bash
   echo $APP_SECRET_KEY
   ```

2. **Check key matches the encryption key:**
   Secrets encrypted with key A cannot be decrypted with key B.

3. **Re-encrypt with current key:**
   ```python
   from sprigconfig.lazy_secret import LazySecret

   new_encrypted = LazySecret.encrypt("my-secret", key)
   ```

---

## Getting Help

If you encounter issues during migration:

1. **Check the [CHANGELOG](../CHANGELOG.md)** for version-specific notes
2. **Review the [FAQ](https://dgw-software.gitlab.io/sprig-config/faq/)**
3. **File an issue** on [GitLab](https://gitlab.com/dgw_software/sprig-config/-/issues)

---

## Future Migrations

### Preparing for 2.0.0

SprigConfig 2.0.0 (tentative) may introduce:

- Plugin system with stable contracts
- Enhanced validation
- Advanced debugging features

**What to expect:**
- Breaking changes will be clearly documented
- Migration guide will be provided before release
- Deprecation warnings in 1.x versions
- Extended support for 1.x after 2.0 release

Check the [ROADMAP](../ROADMAP.md) for planned features.

---

## Best Practices for Upgrades

1. **Test in development first** - Never upgrade directly in production
2. **Review release notes** - Read the CHANGELOG before upgrading
3. **Run your test suite** - Ensure all tests pass with the new version
4. **Check configuration dumps** - Verify merged config is correct
5. **Monitor after deployment** - Watch for configuration-related errors
6. **Have a rollback plan** - Pin versions in requirements.txt

**Example pinning:**
```txt
# Pin to specific version
sprigconfig==1.2.4

# Or allow patch updates only
sprigconfig~=1.2.0
```

---

## Version History Summary

| Version | Release Date | Key Changes | Breaking |
|---------|--------------|-------------|----------|
| 1.2.4   | 2025-12-21   | TOML feature parity | No |
| 1.2.0   | 2025-12-20   | TOML support, merge order fix | No |
| 1.1.0   | 2025-12-15   | JSON support | No |
| 1.0.0   | 2025-12-02   | Initial stable release | N/A |

See [CHANGELOG](../CHANGELOG.md) for complete version history.



---

# File: sprig-config-module/docs/release_checklist.md

# 🧩 SprigConfig — Release Checklist

A repeatable checklist for publishing **SprigConfig** releases  
(from development → tag → CI/CD → package registry).

---

## 🧱 1️⃣  Prep & Verify

- [ ] Ensure all tests pass locally:
  ```bash
  poetry run pytest
  ```
- [ ] Verify coverage and logs:
  ```bash
  poetry run pytest --cov=src --maxfail=1 -q
  ```
- [ ] Confirm version bump in:
  - `pyproject.toml`
  - `src/sprigconfig/__init__.py` (if defined)
- [ ] Update `CHANGELOG.md`
  - Add a new section for the release.
  - Move unreleased changes under `[x.y.z] - YYYY-MM-DD`.

---

## 🧪 2️⃣  Build & Validate Artifacts

- [ ] Clean build directories:
  ```bash
  rm -rf dist/ build/
  ```
- [ ] Build the package:
  ```bash
  poetry build
  ```
- [ ] Verify `.whl` and `.tar.gz` files in `/dist`:
  ```bash
  ls -lh dist/
  ```

---

## 🗾 3️⃣  Commit & Tag

- [ ] Commit the version bump and changelog:
  ```bash
  git add pyproject.toml CHANGELOG.md
  git commit -m "chore(release): prepare v1.x.x"
  ```
- [ ] Create an annotated tag:
  ```bash
  git tag -a v1.x.x -m "🎉 SprigConfig x.x.x — Release notes here"
  ```
- [ ] Push commit + tag:
  ```bash
  git push origin main --tags
  ```

---

## 📦 4️⃣  Verify CI/CD & Publish

- [ ] Check the **GitLab Pipeline**:
  - ✅ Lint
  - ✅ Tests
  - ✅ Security Scans
  - ✅ Build artifacts (wheel + sdist)
- [ ] Confirm package appears in the GitLab **Package Registry**:
  <https://gitlab.com/dgw_software/sprig-config/-/packages>
- [ ] Optional: publish manually to PyPI (if public):
  ```bash
  poetry publish --build --username __token__ --password $PYPI_TOKEN
  ```

---

## 🚀 5️⃣  Post-Release Tasks

- [ ] Verify installation works:
  ```bash
  pip install sprig-config==x.x.x
  ```
- [ ] Announce release:
  - Update **README.md** “Latest Version” badge if applicable
  - Post tag URL to project log or LinkedIn
- [ ] Create next placeholder in `CHANGELOG.md`:
  ```markdown
  ## [Unreleased]
  - Upcoming features and fixes
  ```

---

### ✅ Summary

| Stage | Purpose | Status |
|--------|----------|---------|
| Prep | Ensure version, changelog, tests are ready | ☑ |
| Build | Generate clean, verifiable artifacts | ☑ |
| Tag | Create annotated version tag | ☑ |
| CI/CD | Confirm successful pipeline + registry upload | ☑ |
| Post | Verify install, update docs, announce release | ☑ |

---

**Stable. Secure. Predictable.**




---

# File: sprig-config-module/examples/README.md

# SprigConfig Examples

This directory contains practical examples demonstrating common SprigConfig usage patterns.

## Examples

### 1. Basic Usage (`basic/`)
Simple configuration loading with YAML files.

**Learn:** Basic config file structure and loading

### 2. Profile-Based Configuration (`profiles/`)
Using profiles (dev, test, prod) to override configuration values.

**Learn:** Profile overlays, runtime profile selection

### 3. Secrets Management (`secrets/`)
Secure handling of sensitive data using encrypted secrets.

**Learn:** ENC() format, LazySecret, key management

### 4. Imports (`imports/`)
Organizing configuration across multiple files with recursive imports.

**Learn:** Import syntax, merge behavior, cycle detection

### 5. Environment Variables (`environment-vars/`)
Dynamic configuration using environment variable expansion.

**Learn:** ${VAR} syntax, defaults, .env files

### 6. Web Application (`web-app/`)
Integrating SprigConfig with Flask/FastAPI web frameworks.

**Learn:** Framework integration, configuration singleton, production patterns

### 7. CLI Application (`cli-app/`)
Building command-line tools with configurable behavior.

**Learn:** CLI integration, argument overrides, configuration inspection

## Running the Examples

Each example directory contains:
- `README.md` - Detailed explanation and instructions
- Configuration files (YAML/JSON/TOML)
- Python scripts demonstrating usage
- `.env.example` - Environment variable templates (where applicable)

To run an example:

```bash
cd examples/<example-name>
# Install SprigConfig if not already installed
pip install sprigconfig
# Follow instructions in the example's README.md
python example.py
```

## Requirements

- Python 3.13+
- SprigConfig 1.2.4+

## Learning Path

If you're new to SprigConfig, we recommend following the examples in order:

1. Start with **Basic Usage** to understand core concepts
2. Move to **Profiles** to learn environment-specific configuration
3. Explore **Imports** for organizing larger configurations
4. Try **Environment Variables** for dynamic values
5. Study **Secrets** for handling sensitive data
6. Check **Web Application** or **CLI Application** based on your use case

## Additional Resources

- [Official Documentation](https://dgw-software.gitlab.io/sprig-config/)
- [GitHub Repository](https://gitlab.com/dgw_software/sprig-config)
- [PyPI Package](https://pypi.org/project/sprigconfig/)



---

# File: sprig-config-module/examples/basic/README.md

# Basic Usage Example

This example demonstrates the simplest SprigConfig usage pattern: loading configuration from a single YAML file.

## Files

- `config/application.yml` - Main configuration file
- `example.py` - Python script demonstrating config loading

## What You'll Learn

- Basic configuration file structure
- Loading configuration with `load_config()`
- Accessing configuration values using dict-like syntax
- Using dotted-key access for nested values

## Running the Example

```bash
python example.py
```

## Expected Output

```
Database Configuration:
  Host: localhost
  Port: 5432
  Database: myapp_db

Application Settings:
  Debug: True
  Max Connections: 100

Using dotted-key access:
  db.host = localhost
  app.debug = True
```

## Key Concepts

### Configuration File Structure

SprigConfig uses standard YAML syntax with nested dictionaries:

```yaml
database:
  host: localhost
  port: 5432
  name: myapp_db

app:
  debug: true
  max_connections: 100
```

### Loading Configuration

```python
from sprigconfig import load_config

# Load from default location (./config/)
cfg = load_config()

# Access values
db_host = cfg["database"]["host"]
# or using dotted-key syntax
db_host = cfg.get("database.host")
```

## Next Steps

- Try the **profiles** example to learn about environment-specific configuration
- Explore the **imports** example for organizing larger configurations



---

# File: sprig-config-module/examples/profiles/README.md

# Profile-Based Configuration Example

This example demonstrates how to use SprigConfig profiles to manage environment-specific configuration (development, testing, production).

## Files

- `config/application.yml` - Base configuration (shared across all environments)
- `config/application-dev.yml` - Development overrides
- `config/application-test.yml` - Testing overrides
- `config/application-prod.yml` - Production overrides
- `example.py` - Python script demonstrating profile usage

## What You'll Learn

- How profiles override base configuration
- Runtime profile selection
- Deep merge behavior with profile overlays
- Environment-specific settings
- Production safeguards

## Running the Example

```bash
# Run with development profile (default)
python example.py

# Run with test profile
python example.py --profile test

# Run with production profile
python example.py --profile prod
```

## Expected Behavior

### Development Profile
- Debug logging enabled
- Local database connection
- Permissive CORS settings
- Development API endpoints

### Test Profile
- Warning-level logging
- Test database connection
- Automated testing settings
- Mock external services

### Production Profile
- Error-level logging
- Production database with SSL
- Strict security settings
- Real external services

## Key Concepts

### Profile Overlay Pattern

SprigConfig merges configuration in this order:

1. `application.yml` (base configuration)
2. `application-<profile>.yml` (profile-specific overrides)

Values in the profile file **override** corresponding values in the base file using deep merge semantics.

### Runtime Profile Selection

Profiles are determined at runtime (never from config files):

```python
# Explicit profile
cfg = load_config(profile="prod")

# From environment variable
# APP_PROFILE=test
cfg = load_config()

# From pytest context
# Automatically uses "test" when running tests
```

### Best Practices

- **Base file**: Put shared settings in `application.yml`
- **Profile files**: Only include environment-specific overrides
- **Secrets**: Never commit production secrets (use environment variables or encrypted values)
- **Validation**: Production profile requires `application-prod.yml` to exist

## Next Steps

- Try the **secrets** example to learn about secure configuration
- Explore the **imports** example for organizing complex configurations



---

# File: sprig-config-module/examples/secrets/README.md

# Secrets Management Example

This example demonstrates how to securely handle sensitive configuration data using SprigConfig's encrypted secrets feature.

## Files

- `config/application.yml` - Configuration with encrypted secrets
- `config/application-secrets.yml` - Example of profile-specific secrets
- `example.py` - Python script demonstrating secret handling
- `.env.example` - Template for environment variables

## What You'll Learn

- Encrypting secrets with ENC() format
- Lazy secret evaluation (decrypt only when accessed)
- Secret redaction in config dumps
- Managing encryption keys
- Best practices for secret handling

## Setup

1. Generate an encryption key:

```bash
# Using Python
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

2. Set the encryption key as an environment variable:

```bash
export APP_SECRET_KEY="your-generated-key-here"
```

3. Encrypt a secret value:

```python
from sprigconfig.lazy_secret import LazySecret

# Encrypt a value
encrypted = LazySecret.encrypt("my-secret-password", "your-generated-key-here")
print(encrypted)  # ENC(gAAAAA...)
```

## Running the Example

```bash
# Set your encryption key
export APP_SECRET_KEY="your-key-here"

# Run the example
python example.py
```

## Expected Output

```
Configuration with Secrets:
  Database password: [LazySecret - not yet decrypted]
  API key: [LazySecret - not yet decrypted]

Decrypted values (use with caution):
  Database password: my-secret-db-password
  API key: sk-1234567890abcdef

Config dump (secrets are redacted):
{
  "database": {
    "password": "**REDACTED**"
  },
  "api": {
    "key": "**REDACTED**"
  }
}
```

## Key Concepts

### ENC() Format

Secrets are stored in configuration files using the `ENC()` format:

```yaml
database:
  password: ENC(gAAAAABm...)  # Encrypted ciphertext
```

### LazySecret Objects

When SprigConfig loads a config file with `ENC()` values, it creates `LazySecret` objects:

- **Not decrypted automatically** - prevents accidental exposure
- **Decrypt on demand** - call `.get()` to decrypt
- **Automatic redaction** - not shown in logs or config dumps

### Example Usage

```python
from sprigconfig import load_config

cfg = load_config()

# The secret is still encrypted at this point
db_password = cfg["database"]["password"]  # LazySecret object

# Decrypt only when needed
actual_password = db_password.get()  # "my-secret-password"
```

### Security Best Practices

1. **Never commit encryption keys** - use environment variables
2. **Use different keys per environment** - dev, test, prod
3. **Rotate keys periodically** - re-encrypt secrets with new keys
4. **Minimize secret access** - decrypt only when absolutely needed
5. **Use environment variables for production** - instead of encrypted files
6. **Audit secret access** - log when secrets are decrypted

### Key Management

SprigConfig supports multiple key sources:

1. **Environment variable** (recommended):
   ```bash
   export APP_SECRET_KEY="your-key-here"
   ```

2. **Global key provider**:
   ```python
   from sprigconfig.lazy_secret import LazySecret

   LazySecret.set_global_key_provider(lambda: get_key_from_vault())
   ```

3. **Per-secret key** (advanced):
   ```python
   secret.get(key="specific-key-for-this-secret")
   ```

## Common Use Cases

### Development
- Encrypt non-sensitive mock values
- Share encrypted configs in version control
- Each developer has their own encryption key

### Testing
- Use test-specific keys
- Encrypt test credentials for CI/CD
- Verify secret handling behavior

### Production
- Use environment variables for secrets (preferred)
- Or use encrypted configs with keys from secret management service
- Implement key rotation strategy

## Next Steps

- Read the [Security Documentation](https://dgw-software.gitlab.io/sprig-config/security/)
- Check `docs/SprigConfig_ENC_BestPractices.md` for advanced patterns
- Try the **web-app** example to see secrets in a real application



---

# File: sprig-config-module/examples/web-app/README.md

# Web Application Integration Example

This example demonstrates how to integrate SprigConfig with a Flask web application for profile-based configuration management.

## Files

- `config/application.yml` - Base web app configuration
- `config/application-dev.yml` - Development overrides
- `config/application-prod.yml` - Production overrides
- `app.py` - Flask application with SprigConfig integration
- `requirements.txt` - Python dependencies

## What You'll Learn

- Integrating SprigConfig with Flask
- Using configuration singleton for web apps
- Profile-based deployment (dev vs prod)
- Environment-specific settings
- Configuration dependency injection

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run in development mode:

```bash
python app.py
# or
APP_PROFILE=dev python app.py
```

3. Run in production mode:

```bash
APP_PROFILE=prod python app.py
```

## Expected Behavior

### Development Mode
- Runs on http://localhost:5000
- Debug mode enabled
- Verbose logging
- CORS enabled for local development
- Uses development database

### Production Mode
- Runs on configured host/port
- Debug mode disabled
- Error-level logging only
- Restricted CORS origins
- Uses production database with connection pooling

## Key Concepts

### Configuration Singleton

In web applications, you typically want to load configuration once at startup:

```python
from sprigconfig import load_config

# Load once at application startup
cfg = load_config()

# Access throughout your application
app.config['DATABASE_URL'] = cfg['database']['url']
```

### Profile Selection

Profile is determined by:
1. `APP_PROFILE` environment variable
2. Command line argument
3. Default: 'dev'

```bash
# Development
APP_PROFILE=dev python app.py

# Production
APP_PROFILE=prod gunicorn app:app
```

### Flask Integration Pattern

```python
from flask import Flask
from sprigconfig import load_config

# Load configuration
cfg = load_config()

# Create Flask app
app = Flask(__name__)

# Configure from SprigConfig
app.config['DEBUG'] = cfg.get('app.debug', False)
app.config['DATABASE_URL'] = cfg['database']['url']
```

### Best Practices

1. **Load config early** - Before creating the Flask app
2. **Use config singleton** - Don't reload on every request
3. **Environment variables** - Override config with APP_PROFILE
4. **Secrets management** - Use LazySecret for sensitive values
5. **Validation** - Validate required config on startup

## Running with Gunicorn (Production)

```bash
# Set production profile
export APP_PROFILE=prod

# Run with Gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 app:app
```

## Testing Different Profiles

```bash
# Test development config
curl http://localhost:5000/config

# Check health endpoint
curl http://localhost:5000/health
```

## Common Patterns

### Database Connection

```python
# Get database URL from config
db_url = cfg['database']['url']

# Or build from components
db_url = f"postgresql://{cfg['database']['username']}:{cfg['database']['password'].get()}@{cfg['database']['host']}:{cfg['database']['port']}/{cfg['database']['name']}"
```

### Feature Flags

```python
if cfg.get('features.enable_analytics'):
    initialize_analytics()

if cfg.get('features.enable_caching'):
    setup_cache(cfg['cache']['ttl_seconds'])
```

### CORS Configuration

```python
from flask_cors import CORS

if cfg.get('security.cors_enabled'):
    CORS(app, origins=cfg['security']['cors_origins'])
```

## Next Steps

- Check the **cli-app** example for command-line tool integration
- Review the **secrets** example for handling sensitive configuration
- See the **imports** example for organizing large configurations



---

# File: sprig-config-module/src/sprigconfig/__init__.md

# sprigconfig/__init__.py — Public API Documentation

This document explains the purpose, design goals, and expected behavior of the `sprigconfig.__init__` module.  
It corresponds directly to the source file:

```
sprigconfig/__init__.py
```

---

## Purpose

The `sprigconfig.__init__` module defines the **public API surface** of the SprigConfig package.  
Only stable, supported, externally consumable classes and functions are exported here.

Anything *not* listed in `__all__` is treated as **internal**, meaning its behavior may change without notice.

---

## Public API Exports

### 1. `Config`
A wrapper around deeply nested dictionaries that provides:

- dict-like access  
- dotted-key lookup (`cfg.get("a.b.c")`)  
- safe serialization  
- automatic wrapping of nested dicts into `Config`

This is the primary runtime config object returned by all loading mechanisms.

---

### 2. `ConfigLoader`
The main config-loading engine.  
Responsibilities include:

- Reading YAML files  
- Applying profile overlays  
- Resolving imports  
- Performing deep merges  
- Injecting runtime metadata under `sprigconfig._meta`

All new functionality flows through `ConfigLoader`.

---

### 3. `ConfigSingleton`
A thread-safe, Java-style configuration cache used by components that want a single global config instance.

Key capabilities:

- `initialize(profile, config_dir)`  
- `get()`  
- `reload_for_testing()`  
- `_clear_all()` (test-only)

It is fully optional—projects may use `load_config()` instead.

---

### 4. `deep_merge`
A standalone dictionary merge helper.  
Maintained for backward compatibility with older ETL-service code.

- Deep, recursive  
- Lists overwrite, not append  
- Behaves exactly as older versions did

---

### 5. `ConfigLoadError`
The canonical exception type for *all* config loader errors.

Raised for:

- Missing or invalid YAML  
- Circular imports  
- Failed secrets decryption  
- Invalid profile usage  
- Singleton misuse

---

### 6. `load_config()`
The **legacy API**, preserved to avoid breaking older code.

```python
cfg = load_config(profile="dev", config_dir="/path/to/config")
```

Behavior:

- Delegates internally to `ConfigLoader`  
- Always returns a `Config` instance (never a raw dict)  
- Raises `ConfigLoadError` if something unexpected happens  
- Fully backward compatible  

This ensures existing ETL-service-web code continues to work unchanged.

---

## Backward Compatibility Guarantees

This module explicitly protects older integrations by ensuring:

### ✔ Import patterns still work:
```python
from sprigconfig import load_config, deep_merge
```

### ✔ `load_config()` returns a mapping-like object  
Even though the object is now a `Config`, not a raw dictionary.

### ✔ `deep_merge()` remains stable  
No behavioral changes were introduced in RC3.

---

## Design Principles Reflected in `__init__`

1. **Explicit public API**  
   Only documented and intentionally supported interfaces appear in `__all__`.

2. **Stable surface, flexible internals**  
   Internal refactoring does not affect consuming code.

3. **Clear upgrade path**  
   New projects should use `ConfigLoader` directly; old projects may continue using `load_config()`.

4. **Runtime safety**  
   Defensive check ensures loader always returns a `Config`.

---

## `__all__` Reference

```
__all__ = [
    "Config",
    "ConfigLoader",
    "ConfigSingleton",
    "deep_merge",
    "ConfigLoadError",
    "load_config",
]
```

If it isn’t in this list, it is *not* part of the public API.

---

# Summary

The `sprigconfig.__init__` module acts as the official boundary of SprigConfig’s public interface.  
It guarantees compatibility for old codebases while enabling newer, more powerful features through `ConfigLoader`, `Config`, and `ConfigSingleton`.

It ensures that SprigConfig remains:

- predictable  
- stable  
- backward compatible  
- safe for long-term enterprise use  

---

If you want, I can generate matching API docs for the rest of the package (ConfigLoader, Config, Singleton, deep_merge), or assemble everything into a single combined PDF or MD manual.



---

# File: sprig-config-module/src/sprigconfig/cli.md

# sprigconfig/cli.py — Documentation

This module implements the command-line interface (CLI) for **SprigConfig**, providing a clean, scriptable way to inspect the fully merged configuration produced by `ConfigLoader`.

---

## Overview

The CLI exposes one primary command:

```
sprigconfig dump
```

This command loads configuration from a specified directory, applies profile overlays and imports, resolves secrets (optionally), and outputs the final merged configuration in YAML or JSON.

The CLI is intentionally simple and safe:
- It will refuse to reveal decrypted secrets unless explicitly requested.
- YAML output is always clean and human-readable (no Python object wrappers).
- Errors always produce a non-zero exit code.
- Help output is always available and never depends on application configuration.

---

## Help and Discoverability

The CLI provides first-class, code-defined help behavior:

### Top-level help

```
sprigconfig --help
```

Displays the list of available subcommands with short descriptions. This allows users to discover functionality without trial-and-error.

### Command-specific help

```
sprigconfig dump --help
```

Displays:
- Required and optional arguments
- Clear usage syntax
- Embedded, real-world examples

### Bare command behavior

Running a command without required arguments:

```
sprigconfig dump
```

Will display the command help and examples instead of failing immediately. This avoids argparse’s default “error-first” UX and guides the user toward correct usage.

All help text is defined in code and versioned with the CLI, ensuring it is always available and cannot be broken by missing external files.

---

## Internal Structure

The file is composed of the following pieces:

---

### `_render_pretty_yaml(data)`

Formats Python dictionaries into *clean*, *stable*, and *human-friendly* YAML, with:
- `sort_keys=False` to preserve semantic order
- block-style (`default_flow_style=False`)
- consistent indentation & Unicode handling

This avoids PyYAML's intrusive object tags and ensures round-trip stability.

---

### `_extract_data_for_dump(config, reveal_secrets)`

Converts a SprigConfig `Config` object to a plain dict suitable for serialization.

Key details:

- Calls `Config.to_dict(reveal_secrets=...)`, guaranteeing safe primitive structures.
- Walks the structure recursively:
  - Converts `LazySecret` to either plaintext (`reveal_secrets=True`) or `"ENC(**REDACTED**)"`.
  - Normalizes lists and nested dictionaries.
- Ensures no Python object wrappers (e.g., `!!python/object`) appear in YAML.

This function guarantees that CLI output is production-safe and reusable.

---

### `run_dump(...)`

This is the main execution path for the `dump` command.

Responsibilities:

1. Loads configuration via:
   ```python
   loader = ConfigLoader(config_dir=config_dir, profile=profile)
   config = loader.load()
   ```
2. Captures `ConfigLoadError` and emits a clean message to stderr.
3. Converts config into a clean structure via `_extract_data_for_dump`.
4. Renders the structure as:
   - pretty YAML (`_render_pretty_yaml`)
   - pretty JSON (`json.dumps(..., indent=2)`)
5. Writes to:
   - `stdout`, or
   - an explicitly provided output file (`--output`)

This function is designed for scripting and automated debugging.

---

## The CLI Entry Point (`main()`)

The CLI is built using `argparse` with a subcommand system.

### Subcommand: `dump`

Args:

| Flag | Meaning |
|------|---------|
| `--config-dir PATH` | Required. Directory containing `application.yml` and profiles. |
| `--profile NAME` | Required. Profile to load (e.g., dev, prod, test). |
| `--secrets` | Reveal decrypted secrets (**unsafe**). |
| `--output PATH` | Write output to a file instead of stdout. |
| `--output-format {yaml,json}` | YAML by default; JSON available. |

Example usages printed directly in the help text include:

```
sprigconfig dump --config-dir=config --profile=dev
sprigconfig dump --config-dir=config --profile=prod --secrets
sprigconfig dump --config-dir=config --profile=test --output-format=json
sprigconfig dump --config-dir=config --profile=dev --output out.yml
```

---

## Execution Flow Summary

```
User runs CLI →
 argparse parses args →
  main() dispatches command →
   run_dump() executes →
    ConfigLoader loads config →
     merge/import/profile logic applied →
      Config returned →
   _extract_data_for_dump() normalizes structure →
 Final result pretty-printed as YAML/JSON
```

---

## Why This CLI Exists

SprigConfig’s merging system can be complex:

- base → profile → imported files
- nested imports
- secrets
- metadata tracking (`sprigconfig._meta`)

Developers need a deterministic way to inspect the *final* resolved config tree.
The `dump` CLI provides exactly that:

✔ Debug merging issues  
✔ Verify correct environment expansion  
✔ Confirm profile overlays  
✔ Audit imported file order  
✔ Script config validation in CI pipelines  

It is intentionally simple, safe, and predictable.

---

## Notes for Future Enhancements

- Add `--trace` to print the import graph visually.
- Add `--schema` support for validation before printing.
- Potential integration with `ConfigSingleton` for runtime introspection.

---

Generated documentation for `sprigconfig/cli.py`.



---

# File: sprig-config-module/src/sprigconfig/config.md

# config.md

Documentation for `sprigconfig/config.py`.

## Overview

`Config` is the core immutable-ish mapping wrapper used throughout SprigConfig.  
It provides:

- Dict-like behavior (`keys`, `items`, iteration, containment)
- Deep recursive wrapping of nested dictionaries
- Dotted-key lookup (`cfg["a.b.c"]` or `cfg.get("a.b.c")`)
- Safe conversion to plain dictionaries with optional secret redaction
- YAML dumping with optional pretty-printing and secret handling

---

## Class: `Config`

### ### Initialization

```python
cfg = Config(data: dict)
```

- Must wrap a `dict`; otherwise `TypeError` is raised.
- All nested dicts and lists are recursively wrapped.

---

## Internal Wrapping

`_wrap(obj)` recursively converts:

- dict → `{k: Config-wrapped-value}`
- list → `[wrapped values]`
- Config → returned unchanged
- primitive → returned unchanged

This ensures consistency so that any nested dict automatically becomes a `Config`.

---

## Mapping Behavior

### `__getitem__(key)`
Supports:
- `cfg["a.b.c"]` (dotted key lookup)
- `cfg["a"]["b"]["c"]` (nested access)
- Raises `KeyError` if any part is missing.

When the resolved value is a dict, a new `Config` instance is returned.

### `__contains__(key)`
Returns `True` if the dotted key or normal key resolves.

### `__len__` / `__iter__`
Standard mapping behavior.

---

## Dotted-Key Access

### `get(key, default=None)`

- Resolves dotted paths (“a.b.c”)
- Returns `default` if missing
- Returns nested `Config` for dict nodes

Example:

```python
cfg.get("etl.jobs.root")
```

---

## Serialization: `to_dict()`

```python
cfg.to_dict(reveal_secrets=False)
```

Produces a deep plain-Python dictionary.

Secret handling:

- If `reveal_secrets=False`:  
  LazySecret → `"<LazySecret>"`
- If `reveal_secrets=True`:  
  Decrypts via `LazySecret.get()` or raises `ConfigLoadError` if decryption fails.

---

## YAML Dumping

### `dump(path=None, safe=True, pretty=True, sprigconfig_first=False)`

- `path=None`: returns YAML string
- `path=Path`: writes YAML to file
- `safe=True`: redact LazySecret values
- `safe=False`: reveal secrets (unsafe) or raise on failure
- `pretty=True`: block-style YAML
- `sprigconfig_first=True`: reorder `"sprigconfig"` key to appear first

---

## Error Handling

### `ConfigLoadError`
Raised when:
- secrets cannot be decrypted during unsafe output
- dump-to-file fails

---

## Representation

`__repr__` shows the internal wrapped structure for debugging.

---

## Summary

`Config` is a lightweight but powerful immutable configuration wrapper enabling:

- Protected config state
- Human-friendly dotted-key access
- Secure serialization
- Optional redaction of secrets
- Safe, structured YAML output

It is one of the core building blocks for SprigConfig’s loading pipeline.




---

# File: sprig-config-module/src/sprigconfig/config_loader.md

# sprigconfig/config_loader.py — Explanation and Purpose

This document explains the purpose, design, and behavior of `ConfigLoader`, the core configuration-loading engine for **SprigConfig**.

`ConfigLoader` is responsible for turning a directory of configuration files into a single, deeply-merged, environment-aware, import-traceable configuration object.

---

## 1. What `ConfigLoader` Is For

SprigConfig aims to reproduce the power and ergonomics of Spring Boot–style configuration loading, but in Python.

`ConfigLoader` is the component that:

* Loads a base configuration (`application.<ext>`)
* Applies a runtime profile overlay (`application-<profile>.<ext>`)
* Expands `${ENV}` variables inside configuration files
* Follows recursive `imports:` statements across multiple files
* Detects circular imports
* Deep-merges structures with clear override semantics
* Wraps encrypted values (`ENC(...)`) with `LazySecret` objects
* Adds internal metadata so applications can introspect how the configuration was built

It is the **heart of SprigConfig**, turning a folder of modular configuration sources into a structured, immutable configuration tree.

---

## 2. Supported Configuration Formats

`ConfigLoader` is **format-agnostic**.

SprigConfig currently supports:

* YAML (`.yml`, `.yaml`)
* JSON (`.json`)
* TOML (`.toml`)

Exactly **one format is active per run**. The active format is determined by the following precedence:

1. An explicit `config_format=` argument passed to `ConfigLoader`
2. The `SPRIGCONFIG_FORMAT` environment variable
3. A default of `yml` if neither is provided

All configuration files involved in a single load (base file, profile overlay, and imports) **must use the active format**. Mixing formats within a single run is intentionally not supported.

**Note on TOML**: When using TOML format, the `imports` directive must be placed at the root level before any table headers (e.g., `[app]`) due to TOML syntax requirements.

---

## 3. Why This File Exists

Python has no native configuration loading standard as powerful as Spring Boot.

Real systems need:

* Profiles (dev, test, prod, etc.)
* Separation between base config and overrides
* Secrets that are not eagerly decrypted
* Modular configuration via file imports
* Strong cycle detection when imports chain together
* A way to trace *exactly how* the final config was constructed
  (e.g., for debugging CI failures or misconfigured deployments)

`ConfigLoader` solves these problems by providing:

### ✔ Predictable ordering

Base → profile overlay → imported files in deterministic merge order.

### ✔ Safety

Circular imports throw explicit `ConfigLoadError`.

### ✔ Transparency

`_meta.sources` and `_meta.import_trace` reveal every file loaded, in order.

### ✔ Secret hygiene

Encrypted values remain encrypted until accessed, preventing accidental logging.

### ✔ Full reproducibility

Given the same directory, profile, and format, the result is always identical.

---

## 4. High-Level Flow of the Loader

### **Step 1: Load `application.<ext>`**

The base configuration file establishes the root config structure.

It is always loaded first and recorded as the **first entry** in the import trace.

---

### **Step 2: Load `application-<profile>.<ext>`**

If a profile overlay exists, it is deeply merged into the base config.

This allows profile-specific overrides, such as:

* Different credentials
* Different host/port values
* Test-specific feature toggles

---

### **Step 3: Apply recursive imports**

Any configuration node may include:

```yaml
imports:
  - imports/common
  - imports/logging
```

**Import Resolution**: Import paths are **extension-less** for portability across formats. The loader automatically appends the active format's extension (`.yml`, `.json`, or `.toml`). This allows the same configuration structure to work across all supported formats without modification.

**Positional Imports**: Imports are **positional** — they merge relative to where the `imports:` key appears in the tree:

* Root-level `imports:` merge at the root
* Nested `imports:` (e.g., `app.imports:`) merge **under that key**
  * If the imported file has `foo: bar`, you get `app.foo: bar`
  * If the imported file has `app: {foo: bar}`, you get `app.app.foo: bar` (nested!)

This positional behavior allows fine-grained control over configuration composition.

**Security**: Import paths are validated to prevent **path traversal attacks**. Imports like `../../etc/passwd` will raise a `ConfigLoadError`. All imports must resolve within the configuration directory.

`ConfigLoader` resolves each import relative to the configuration directory, loads the file using the active format, merges it into the current node, and records the operation.

For each import, the loader tracks:

* Import depth
* Which file imported which
* The order files were processed
* Circular import violations

Imports may appear anywhere in the configuration tree, not just at the root.

---

### **Step 4: Inject the runtime profile**

The loader ensures the active runtime profile is always available under:

```yaml
app:
  profile: <profile>
```

This guarantees the application can introspect the current environment at runtime.

---

### **Step 5: Add internal metadata**

After all merging is complete, the loader injects metadata under:

```yaml
sprigconfig:
  _meta:
    profile: <profile>
    sources: [...]
    import_trace: [...]
```

This metadata supports:

* Debugging configuration merges
* Logging the provenance of runtime settings
* Unit testing and CI verification
* Auditing configuration lineage

---

### **Step 6: Wrap encrypted values**

Any string matching `ENC(...)` is replaced with a `LazySecret` object, for example:

```yaml
db:
  password: ENC(gAAAAABl...)
```

Secrets remain encrypted until explicitly accessed, preventing accidental exposure in logs, dumps, or debug output.

---

## 5. Key Internal Components

### `_load_file(path: Path)`

Reads a configuration file from disk using the active format (YAML, JSON, or TOML), expands environment variables, and returns a Python dictionary. Supports all three formats transparently.

---

### `_resolve_import(import_key: str)`

Resolves an import path by appending the active format's extension if not already present. For example, `imports/common` becomes `imports/common.yml` when using YAML format. Also validates that the resolved path stays within the config directory to prevent path traversal attacks.

---

### `_expand_env(text: str)`

Substitutes `${VAR}` or `${VAR:default}` expressions using environment variables before parsing. Works across all supported formats.

---

### `_apply_imports_recursive(node, ...)`

Walks the entire configuration tree and processes `imports` wherever they appear, maintaining correct import order and cycle detection. Merges imported content **positionally** into the current node where the `imports:` key appears.

---

### `_inject_secrets(data)`

Replaces encrypted values with `LazySecret` wrappers.

---

### `_inject_metadata(merged)`

Populates the `_meta` section with profile, source paths, and detailed import trace information.

---

## 6. Why Import Tracing Matters

Modern deployments depend on:

* CI/CD automation
* Per-environment overlays
* Local developer overrides
* Encrypted secrets

When something behaves unexpectedly, you must be able to answer:

* **Which file set this value?**
* **What order were configs merged in?**
* **Where did this setting originate?**
* **Was something overridden unexpectedly?**

The import trace provides a complete, ordered history of how the final configuration was constructed.

---

## 7. Returned Object: `Config`

The result of `ConfigLoader.load()` is a `Config` object, which:

* Is mapping-like (supports `dict` operations)
* Supports dotted-key lookups (`cfg.get("server.port")`)
* Enforces immutable-ish semantics
* Provides safe `.to_dict()` and `.dump()` behavior
  (secrets are redacted unless explicitly requested)

---

## 8. Summary

`ConfigLoader` provides a **robust, production-grade configuration system** for Python services.

It enables:

* Hierarchical configuration
* Deterministic merges
* Profile-aware overrides
* Secure encrypted secrets
* Full lineage and traceability
* Safety from circular references
* Debuggable, testable configuration behavior

This file is foundational to the SprigConfig project and enables consistent, scalable configuration loading for complex Python applications.



---

# File: sprig-config-module/src/sprigconfig/config_singleton.md

# sprigconfig/config_singleton.py — Explanation and Purpose

This document explains the role of `ConfigSingleton` in SprigConfig, why it exists, what problems it solves, and how application code is expected to interact with it.

---

## 1. What `ConfigSingleton` Is For

SprigConfig’s `ConfigLoader` is powerful but intentionally **not global**.  
Applications typically need one **canonical configuration** loaded at startup and shared everywhere.

In Java/Spring Boot, this is natural—Spring creates a single `ApplicationContext` containing one unified configuration graph.

Python, however, has no built‑in model for:

- Globally‑accessible configuration  
- Enforcing exactly one initialization  
- Preventing accidental reloading  
- Providing a stable config reference across the entire application  

`ConfigSingleton` implements that missing behavior.

It creates **one and only one** global configuration instance for the runtime of the process.

---

## 2. What Problem It Solves

Real apps (APIs, ETL services, schedulers, batch processors) need:

- A single source of truth for external settings  
- Deterministic startup behavior  
- Protection from accidental reinitialization  
- A fast way for any module to fetch the configuration  

Without a singleton, code could easily:

- Load configuration multiple times
- Load with inconsistent directory paths or profiles
- Mutate state unpredictably  
- Cause race conditions in concurrent environments

`ConfigSingleton` ensures **strong guarantees** about configuration lifecycle.

---

## 3. How It Works

### ### Key Behavior

- `initialize(profile, config_dir)`  
  Must be called **exactly once** when the application boots—typically inside a `create_app()` or startup script.

- `get()`  
  Returns the previously loaded `Config` object.  
  If called before initialization, it raises an error to enforce correct startup sequencing.

- `initialize()` is thread‑safe  
  A lock ensures that parallel startup threads cannot race to initialize the config twice.

- Attempts to call `initialize()` more than once always fail  
  This prevents:
  - Accidental reconfiguration  
  - Re-loading from different directories  
  - Tests or background workers from silently resetting config state

- `_clear_all()`  
  This is **strictly for testing**—allowing pytest fixtures to reset the singleton to a blank state before each test.

---

## 4. Class Attributes (Internal Storage)

| Attribute         | Purpose |
|------------------|---------|
| `_instance`      | The global `Config` object returned from `ConfigLoader.load()` |
| `_profile`       | The profile used (dev, prod, test, etc.) |
| `_config_dir`    | Absolute path to the configuration directory |
| `_lock`          | Ensures thread‑safe initialization |

These values remain stable for the entire runtime of the application.

---

## 5. Initialization Flow

### `initialize()`  
1. Validate input arguments  
   - Ensures a real profile string is provided  
   - Ensures `config_dir` resolves to a valid path  

2. Acquire a lock  
   Prevents concurrent initialization.

3. Check whether initialization has already happened  
   - If so → raise `ConfigLoadError`  

4. Create a `ConfigLoader`  
   Pass in `profile` and `config_dir`.

5. Load configuration  
   Result must be a `Config` object.

6. Store configuration in `_instance`  
   Now the entire application can access it.

### `get()`

Simply returns `_instance`.

Throws an error if called before initialization to catch programmer misuse.

---

## 6. Why the Singleton Is Strict

SprigConfig intentionally **does not reload configuration** at runtime.  
Reloading creates:

- Race conditions
- Inconsistent settings halfway through a request or job
- Security concerns (e.g., keys changing mid-process)
- Excessive overhead from repeatedly parsing and merging YAML

A loaded configuration is treated as **immutable** for the lifetime of the process.

This matches:

- Spring Boot semantics  
- Kubernetes/environment-based configuration  
- Production‑grade architecture patterns  

---

## 7. How Applications Should Use It

### Example (FastAPI)

```python
from sprigconfig.config_singleton import ConfigSingleton

def create_app():
    ConfigSingleton.initialize(
        profile=os.getenv("APP_PROFILE", "dev"),
        config_dir="config"
    )

    app = FastAPI()
    return app
```

### Anywhere else in the code:

```python
cfg = ConfigSingleton.get()
db_host = cfg.get("database.host")
```

No module should ever try to reinitialize.

---

## 8. Testing Support

Unit tests often need to:

- Load configuration with different directories
- Use synthetic test profiles
- Reset configuration between test cases

For this reason we expose `_clear_all()`:

```python
ConfigSingleton._clear_all()
```

It wipes the singleton state so the test can start fresh.

This method is **not** for production use.

---

## 9. Summary

`ConfigSingleton` provides a:

- Safe  
- Deterministic  
- Thread‑safe  
- Single‑assignment  

entry point for loading the application's unified configuration.

It ensures:

- No accidental reinitialization  
- No environment drift  
- No inconsistent configs across modules  
- Predictable application startup  

In short, this file enforces **configuration correctness** at the system level and completes SprigConfig’s goal of delivering a Spring‑like configuration experience in Python environments.

---




---

# File: sprig-config-module/src/sprigconfig/deepmerge.md

# sprigconfig/deepmerge.py — Explanation and Purpose

This document describes the purpose, behavior, design rationale, and rules behind the `deep_merge` function used throughout SprigConfig.  
It is one of the core utilities that makes hierarchical configuration loading predictable, transparent, and safe.

---

## 1. What `deep_merge` Is For

SprigConfig loads configuration from multiple YAML files:

- `application.yml`  
- `application-<profile>.yml` overlays  
- Imported YAML files  
- Optional user overrides

All these files must be **merged** into one coherent configuration dictionary.

Python's built‑in `dict.update()` is not sufficient because it:

- Performs only a shallow merge  
- Overwrites entire nested dictionaries  
- Cannot detect missing partial overrides  
- Provides no logging visibility  

`deep_merge` implements a **canonical**, deterministic, production-safe deep merge algorithm.

---

## 2. Key Design Goals

### ✔ Predictable Merge Semantics  
The same inputs always produce the same merged configuration.

### ✔ Transparency  
Logs explicitly show:
- New keys added  
- Keys overridden  
- Partial overrides (missing keys)  

### ✔ Isolation  
`deep_merge` contains **no SprigConfig-specific logic**, so it:
- Can be unit-tested independently  
- Can be reused by external projects  
- Remains easy to reason about

### ✔ Safe Overrides  
Warns developers when an override file does *not* include keys found in the base file. This prevents accidental partial deletion unless explicitly suppressed.

---

## 3. The Merge Rules

These rules define exactly how configuration structures resolve when multiple sources merge.

### **Rule 1 — Dict + Dict → Recursive merge**
If both base and override values are dictionaries:

- Merge key-by-key  
- Recurse deeper  
- Warn if the override dictionary is missing keys present in the base  

This ensures overlays must be explicit unless warning suppression is enabled.

---

### **Rule 2 — List + List → Override, never append**
Lists do **not** merge element‑by‑element.

Example:

```yaml
base:
  ports: [8000, 8001]

override:
  ports: [9000]
```

Result:

```yaml
ports: [9000]
```

Appending would introduce order ambiguity and non-determinism, so SprigConfig replaces lists entirely.

---

### **Rule 3 — Scalar → Replace**
Integers, strings, booleans, floats, etc. are always overwritten.

---

### **Rule 4 — Missing Key → Add**
If a key exists in the override but not in base, it is added:

Logged as:

```
Adding new config 'path.to.key'
```

---

### **Rule 5 — Existing Key Overwrite → Log**
If a key exists in both base and override and values differ, the override wins.

Logged as:

```
Overriding config 'path.to.key'
```

---

### **Rule 6 — Missing Keys in Override → Warn**
If base has keys that override *does not* include:

Example:

```yaml
base:
  db:
    host: localhost
    port: 5432
    user: admin

override:
  db:
    host: service-db
```

Log warning:

```
Config section 'db' partially overridden; missing keys: {'port', 'user'}
```

This is extremely useful for catching accidental incomplete overrides.

Warnings can be suppressed during:

- Import-heavy configurations  
- Tests where noise is undesirable  
- Environments where missing keys are expected  

---

## 4. Runtime Behavior

### Function signature

```python
deep_merge(base, override, suppress=False, path="")
```

- **`base`** is mutated in-place  
- **`override`** dictates the changes  
- **`suppress=True`** disables all logging/warnings  
- **`path`** keeps track of nested keys for readable logging

Returns the modified base dictionary to allow chaining.

---

## 5. Why It Lives in Its Own Module

The deep merge algorithm must remain:

- Stable
- Reusable
- Easy to test
- Free from circular imports
- Independent of SprigConfig’s higher-level components

`ConfigLoader` depends on this function, but `deepmerge` depends on nothing in return.

This separation ensures a clean architecture consistent with SprigConfig’s design goals.

---

## 6. Example Merge

### Base

```yaml
server:
  host: 0.0.0.0
  port: 8080
  ssl:
    enabled: false
    ciphers: ["TLS_AES"]
```

### Override

```yaml
server:
  port: 9090
  ssl:
    enabled: true
```

### Result

```yaml
server:
  host: 0.0.0.0
  port: 9090
  ssl:
    enabled: true
    ciphers: ["TLS_AES"]
```

Note that `ciphers` stays untouched because the override did not specify it — and a warning is logged.

---

## 7. Summary

`deep_merge` is a critical part of SprigConfig’s configuration logic.  
It ensures:

- Deterministic merging  
- Clear logs and warnings  
- Protection from accidental partial overrides  
- Strong guarantees about final configuration correctness  

Because configuration is security‑critical and controls application behavior, the merge algorithm must be correct, transparent, and predictable — which is exactly what `deep_merge` provides.

---




---

# File: sprig-config-module/src/sprigconfig/exceptions.md

# exceptions.md

## ConfigLoadError

**Location:** `sprigconfig/exceptions.py`

### Purpose
`ConfigLoadError` is the unified exception type raised whenever SprigConfig is unable to load, parse, merge, or otherwise process configuration files.

It intentionally wraps all configuration‑related failures so higher‑level components (e.g., the CLI, FastAPI apps, ETL services) can safely catch a single error type rather than handling multiple low‑level exceptions.

### When It Is Raised
Typical scenarios include:

- Missing `application.yml` or invalid YAML syntax  
- Unresolvable environment variable expansions  
- Circular imports detected during config processing  
- Failure to decrypt secrets when `reveal_secrets=True`  
- Attempting to use `ConfigSingleton` incorrectly (e.g., calling `get()` before `initialize()`)  
- Failure to write a YAML dump to disk  

### Example Usage

```python
from sprigconfig import load_config, ConfigLoadError

try:
    cfg = load_config(profile="dev", config_dir="/etc/app")
except ConfigLoadError as e:
    print(f"Failed to load configuration: {e}")
```

### Design Intent

- **Keeps error handling consistent** across the entire SprigConfig ecosystem.  
- Ensures **clean user-facing error messages** in CLI utilities.  
- Allows developers to catch a *single* exception rather than chasing several possible internal failures.




---

# File: sprig-config-module/src/sprigconfig/help.md

# sprigconfig/help.py — Help Metadata Documentation

This module defines **code-based CLI help metadata** for SprigConfig.

It exists to centralize human-facing help text (summaries and examples) in a
single, version-controlled location, while keeping the CLI bootstrap logic
simple, robust, and free of external file dependencies.

---

## Purpose

`help.py` provides structured metadata used by the CLI to:

- Populate top-level command listings (e.g. `sprigconfig --help`)
- Provide short command summaries
- Display real-world usage examples
- Improve discoverability without argparse boilerplate
- Ensure help output is always available, even in broken environments

This design deliberately avoids external `help.yml` files to prevent
bootstrap fragility and filesystem dependency issues.

---

## Design Principles

The help system follows these rules:

- **Code-defined truth**  
  Help metadata is versioned with the code and cannot go missing.

- **Zero runtime dependencies**  
  No configuration loading, no profiles, no imports, no secrets.

- **Declarative, not procedural**  
  This module contains data only — no logic.

- **CLI-scoped**  
  Help metadata belongs to the CLI layer, not application configuration.

---

## Structure

The module exposes a single public constant:

```python
COMMAND_HELP
```

This is a dictionary keyed by subcommand name.

### Schema

```text
COMMAND_HELP
  └── <command>
       ├── summary   (str)   — short, one-line description
       └── examples  (list)  — realistic CLI usage examples
```

---

## Current Commands

### `dump`

```python
COMMAND_HELP = {
    "dump": {
        "summary": "Dump merged configuration for inspection/debugging",
        "examples": [
            "sprigconfig dump --config-dir=config --profile=dev",
            "sprigconfig dump --config-dir=config --profile=prod --secrets",
            "sprigconfig dump --config-dir=config --profile=test --output-format=json",
            "sprigconfig dump --config-dir=config --profile=dev --output out.yml",
        ],
    }
}
```

#### Summary

> Dump merged configuration for inspection/debugging

#### Examples

```
sprigconfig dump --config-dir=config --profile=dev
sprigconfig dump --config-dir=config --profile=prod --secrets
sprigconfig dump --config-dir=config --profile=test --output-format=json
sprigconfig dump --config-dir=config --profile=dev --output out.yml
```

These examples are displayed directly in CLI help output and are intended to be:

- Copy/paste ready
- Representative of real-world usage
- Safe by default (with explicit opt-in for secrets)

---

## How the CLI Uses This Module

The CLI imports `COMMAND_HELP` at startup and uses it to:

- Populate `argparse` subparser summaries
- Render examples in command-specific help
- Display a friendly command list when no arguments are provided

Because this metadata is pure Python data, it is:

- Always available
- Cheap to import
- Safe during early CLI bootstrap

---

## Extending Help Metadata

When adding a new CLI command:

1. Add a new entry to `COMMAND_HELP`
2. Provide:
   - A concise summary
   - At least one realistic example
3. Wire the command into `cli.py`

No additional files or configuration changes are required.

---

## Why This File Exists (Even Though It’s Small)

Although `help.py` is intentionally minimal, it serves an important role:

- Prevents help text duplication
- Keeps CLI logic readable
- Establishes a clear pattern for future commands
- Enables future doc generation if needed

This file trades a few lines of data for long-term clarity and robustness.

---

Generated documentation for `sprigconfig/help.py`.



---

# File: sprig-config-module/src/sprigconfig/lazy_secret.md

# sprigconfig/lazy_secret.py — Explanation and Purpose

This document explains the design, purpose, and behavior of the `LazySecret` subsystem in SprigConfig, including global key management and secure secret handling.

---

## 1. What `LazySecret` Is For

Modern applications must store secrets (DB passwords, API tokens, encryption keys) inside configuration files — but they *must not* allow these secrets to appear in logs, stack traces, or debug dumps.

SprigConfig solves this by:

- Allowing encrypted values inside YAML (`ENC(...)`)
- Deferring decryption until absolutely necessary (“lazy” decryption)
- Avoiding storing raw secrets in config objects
- Providing strict, secure key resolution rules
- Supporting dynamic key providers (rotation, vault-based loading)

`LazySecret` is therefore the security engine of SprigConfig’s configuration system.

---

## 2. Why This File Exists

Typical config loaders eagerly parse all values. That is dangerous for secrets:

- A stack trace might log the decrypted value.
- A `.dump()` operation could accidentally leak credentials.
- Multiple components might store secrets in unprotected strings.
- Developers may accidentally print configs and leak sensitive data.

SprigConfig’s philosophy:

### **Secrets should not be decrypted unless explicitly requested.**

This file provides:

- The `LazySecret` class  
- Global key management  
- Optional dynamic key provider logic  
- Validation and safe key resolution  
- Backward compatibility for legacy calling code  

---

## 3. Encrypted Config Format

A secret in YAML looks like:

```yaml
db:
  password: ENC(gAAAAABlZx...)
```

`ConfigLoader` wraps that in a `LazySecret` instance instead of decrypting it.

The ciphertext is stored safely until the application explicitly calls `.get()`.

---

## 4. Global Key Management API

### ### `_GLOBAL_KEY`
Stores a single Fernet key used for decrypting all secrets (unless an explicit key is passed).

### `set_global_key(key: str)`
Sets and validates the key immediately.

- Ensures the key is non-empty  
- Ensures the key is a valid base64 Fernet key  
- Prevents invalid cryptographic material from entering the system  

### `get_global_key()`
For diagnostics only — never for normal application use.

### `set_key_provider(provider)`
Allows registering a function that returns a Fernet key dynamically.

Examples:

- Rotating keys
- Fetching from Vault
- Loading from secure hardware storage

### `ensure_key_from_env()`
Utility for lazy initialization based on:

```
APP_SECRET_KEY=<base64key>
```

Useful when applications want SprigConfig to initialize itself before loading configs.

---

## 5. Key Resolution Rules

The function `_resolve_key()` determines which key to use when decrypting a secret.

Priority order:

1. **Explicit key** passed to the `LazySecret` constructor  
2. **Global key** previously set  
3. **Dynamic key provider**, if registered  
4. **Environment variable** `APP_SECRET_KEY`

If none of these provide a usable key, a `ConfigLoadError` is raised.

### Recursion guard
If a key provider indirectly triggers more key resolution, the system detects it and throws an error to prevent infinite loops.

---

## 6. How `LazySecret` Works

The `LazySecret` class wraps encrypted values and decrypts them only when accessed.

### Constructor

```python
LazySecret("ENC(gAAAAA...)")
```

It:

- Strips the `ENC(...)` wrapper
- Stores ciphertext only
- Does *not* decrypt yet

### `.get()`

Returns the decrypted secret value.

### `__str__()`

Also decrypts — but applications should be careful when coercing secrets to strings.

### `.zeroize()`

Attempts to overwrite decrypted material in memory:

```python
mysecret.zeroize()
```

While Python cannot fully guarantee secure memory handling, this is the best-effort equivalent of clearing sensitive buffers.

---

## 7. Why Lazy Decryption Matters

### **Security benefits**

- Secrets do not appear in config dumps  
- Logging the config won’t leak passwords  
- Developers cannot accidentally inspect decrypted values  
- Secrets remain encrypted in memory until use  
- Works cleanly with pytest or debugging tools  

### **Operational benefits**

- Supports key rotation  
- Allows secure runtime environments (e.g., Kubernetes) to inject keys only at startup  
- Ensures consistent behavior across imports, overlays, and deep merges  

---

## 8. Backward Compatibility

Older versions of SprigConfig exposed a symbol named `_key_provider`.  
To maintain compatibility:

```python
if "_key_provider" not in globals():
    def _key_provider():
        return os.getenv("APP_SECRET_KEY")
```

This prevents breaking existing codebases that still reference the legacy name.

---

## 9. Summary

`lazy_secret.py` provides:

- Secure, lazy secret decryption
- Strong global key handling
- Strict validation and error reporting
- Optional dynamic key resolution
- Compatibility with older integrations

It is one of the foundational security components of SprigConfig and ensures that configuration-driven applications can handle secrets safely and predictably.

---




---

# File: sprig-config-module/tests/README_Test_Suite.md


# SprigConfig Test Suite  
**Location:** `sprig-config-module/tests/`  
**Purpose:** Validate the core configuration engine, secret-handling, deep-merge logic, profile overlays, import tracing, CLI behavior, and metadata propagation for SprigConfig.

This test suite is designed to be:

- **Deterministic** – reproducible across machines & CI  
- **Environment-aware** – driven by `APP_CONFIG_DIR`, `.env`, and pytest CLI flags  
- **Debug-friendly** – extensive logging & merged-config dumps  
- **Architecture-verifying** – tests import future public APIs (`ConfigLoader`, `Config`, `LazySecret`, etc.)  
- **High-coverage** – each subsystem has focused tests *plus* full integration routes  

---

# 🧱 Test Suite Structure

```
tests/
│
├── config/                   # Static test config tree used by many fixtures
├── test_logs/                # Log output generated automatically during testing
├── utils/                    # Test utilities, helpers, support modules
│
├── conftest.py               # Global fixtures, CLI flags, serialization helpers
├── conftest.md               # Documentation for conftest.py
│
├── test_cli.py               # Tests for CLI rendering, YAML dump, secret redaction
├── test_cli.md
│
├── test_config.py            # Tests for Config object, dotted-key lookup, immutability
├── test_config.md
│
├── test_config_singleton.py  # Tests for cached/global config singleton behavior
├── test_config_singleton.md
│
├── test_deep_merge.py        # Deep merge algorithm tests
├── test_deep_merge.md
│
├── test_import_trace.py      # Tests for recursive imports + detection of cycles
├── test_import_trace.md
│
├── test_integration.py       # End-to-end config loading with overlays, imports, meta
├── test_integration.md
│
├── test_meta.py              # Tests for _meta generation (sources, profile, trace)
├── test_meta.md
│
├── test_meta_sources.py      # Focused tests on metadata source annotations
├── test_meta_sources.md
│
├── test_profiles.py          # Profile overlay resolution, precedence, overrides
├── test_profile_behavior.md
│
└── .env                      # Optional test-time environment file
```

---

# 🔍 Overview of Technologies Used

### **1. Pytest**
Used for:

- Fixture dependency injection  
- Parameterized testing  
- CLI extension (`pytest_addoption`)  
- Conditional test skipping  

### **2. YAML + JSON Handling**
SprigConfig uses:

- `yaml.safe_load` / `safe_dump`  
- A custom deep merge implementation  
- Redaction and safe serialization wrappers  

### **3. Environment-Based Config Loading**
Tests validate:

- `APP_CONFIG_DIR` discovery  
- `.env` loading using python-dotenv  
- The `--env-path` override for test-time `.env` selection  

### **4. Secret Handling**
Using `LazySecret` with:

- Safe, redacted serialization  
- Optional secret resolution (`--dump-config-secrets`)  
- Optional plaintext dump (`--dump-config-no-redact`)  

### **5. Logging**
Full-session debug logs are produced:

```
test_logs/pytest_<timestamp>.log
```

containing:

- Trace-level diagnostics  
- Import maps  
- Merge order  
- File resolutions  

---

# 🚀 Pytest CLI Options (“Adoption Flags”)

These allow configurable behavior during test runs:

| Flag | Purpose |
|------|---------|
| `--env-path <file>` | Override which `.env` file tests use |
| `--dump-config` | Print merged config for each test |
| `--dump-config-format yaml|json` | Select print format |
| `--dump-config-secrets` | Resolve LazySecret values before printing |
| `--dump-config-no-redact` | Output plaintext secrets |
| `--debug-dump <file>` | Write merged config snapshot after test |
| `RUN_CRYPTO=true` | Run crypto-heavy tests |

---

# 🧪 Test Categories

## **1. Config Object & API**
`test_config.py`, `test_config_singleton.py`

Ensures:

- Dotted-key lookup  
- Deep copying  
- Immutability guarantees  
- Consistent `.to_dict()` round-tripping  

---

## **2. Deep Merge Algorithm**
`test_deep_merge.py`

Validates:

- Overlays  
- Replacement semantics  
- Collision rules  
- Recursive merge behavior  

---

## **3. Import Tracing**
`test_import_trace.py`

Ensures:

- Recursive file imports  
- Cycle detection  
- Metadata chain-building  

---

## **4. Profiles (application-<profile>.yml)**
`test_profiles.py`

Covers:

- File precedence  
- Profile inheritance  
- Environment-driven selection  

---

## **5. Metadata Plumbing**
`test_meta.py`, `test_meta_sources.py`

Ensures:

- Source tracking  
- Import trace awareness  
- Storage in:  
  ```
  sprigconfig._meta
  ```

---

## **6. CLI Behavior**
`test_cli.py` validates:

- Pretty YAML output  
- Redacted vs resolved secret output  
- CLI error messaging  

---

## **7. Full Integration Tests**
`test_integration.py`

Simulates:

- Real config directory  
- Overlays  
- Imports  
- Metadata  
- LazySecret injection  
- Environment discovery  

This is the closest to real runtime behavior.

---

# 🔧 Running the Test Suite

Run all tests:

```
pytest
```

Enable debug logging + see merged configs:

```
pytest --dump-config
```

Use a custom `.env` file:

```
pytest --env-path=tests/.env.dev
```

Capture merged config snapshots:

```
pytest --debug-dump=/tmp/config.yml
```

Run crypto tests:

```
RUN_CRYPTO=true pytest
```

---

# 🧩 Adding New Tests

Follow this pattern:

1. Create a `.py` test file  
2. Create a `.md` file with the same name (optional but recommended)  
3. If tests need a config tree:  
   - Use `full_config_dir` or  
   - Create a temporary directory  
4. If coverage touches import or overlay behavior, include:  
   ```
   cfg = capture_config(lambda: ConfigLoader(...).load())
   ```  
   This ensures `.yml` snapshots can be captured.

---

# 📎 Notes

- **Do not** modify `tests/config/` during tests — use `full_config_dir` instead.  
- All `.md` files in the test suite are **developer documentation**, not used by pytest.  
- `conftest.py` is the authoritative specification of test mechanics.  

---

# ✔️ Final Thoughts

SprigConfig’s test suite is intentionally *dense* and *diagnostic-rich*.  
It exists not just to assert correctness, but to illuminate exactly:

- how configs merge  
- where imports originate  
- how metadata propagates  
- how environment variables influence resolution  
- and how secrets are safely handled  

This ensures the configuration engine remains predictable, secure, and transparent — even as the architecture evolves.




---

# File: sprig-config-module/tests/config/rules_for_config.md

# SprigConfig Configuration Rules

This document describes how the system should interpret and process configuration files using `sprigconfig`. The rules below define how base configs, profile overlays, and imports should be handled to generate a final configuration structure.

## 1. YAML Structure Used As-Is
Every key in YAML files is interpreted literally. Keys such as `app:` are not treated specially. They follow the same merge rules as any other key.

## 2. Deep Merge Behavior
- **Mapping + Mapping** → deep-merged recursively  
- **List + List** → lists are overwritten by the later value  
- **Scalar + Scalar** → overwritten by the later value  

## 3. Merge Order (Final Precedence)
1. `application.yml`  
2. Imports from `application.yml` (recursive)  
3. `application-<profile>.yml`  
4. Imports from `application-<profile>.yml` (recursive)  

## 4. Handling of Imports
Only the YAML files listed via `imports:` are included. Other files are ignored.

## 5. Profile Files
The system recognizes any file named using:
```
application-<profile>.yml
```
The runtime profile selects which of these files is loaded.

## 6. Metadata Injection
SprigConfig adds a `_meta` object under the `sprigconfig:` root to track:
- The runtime profile used to generate the config
- The list of all files that were merged in order

Example:
```
sprigconfig:
  _meta:
    profile: dev
    files:
      - application.yml
      - application-dev.yml
      - imports/common.yml
```

This `_meta` data is the only extra information added by SprigConfig. The rest of the configuration is strictly a result of merging YAML files.



---

# File: sprig-config-module/tests/conftest.md


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




---

# File: sprig-config-module/tests/test_cli.md

# Documentation for `tests/test_cli.py`

This document explains the purpose and functionality of the CLI integration
tests found in:

```
tests/test_cli.py
```

These tests validate the command‑line interface for SprigConfig, ensuring that
the CLI behaves correctly when invoked as a subprocess and that configuration
output is accurate.

---

# 🎯 Purpose of `test_cli.py`

The SprigConfig CLI provides a user‑facing way to:

- Load configuration files  
- Merge base and profile layers  
- Resolve imports  
- Format output in YAML or JSON  
- Write merged config to stdout or a file  

These tests verify that the CLI behaves correctly in an environment that mimics
real shell usage.

Because the CLI runs in a **separate process**, these tests use `subprocess.Popen`
to capture its exit code, stdout, and stderr exactly as a user would see them.

---

# 🧪 1. Autouse Fixture: `disable_logging_handlers`

```python
@pytest.fixture(autouse=True)
def disable_logging_handlers():
```

### Purpose:
Ensures that when the CLI runs as a subprocess, **no logging handlers bleed into
stdout or stderr**.

The fixture:

- Removes global logging handlers before each test  
- Restores them after the test  

### Why this matters:
The CLI’s output must be **clean YAML/JSON**, with **no logging noise**, so that
the output can be piped into tools like `cat`, `jq`, or other scripts.

---

# ⚙️ 2. Helper Function: `run_cli(args, cwd)`

This function launches the CLI via:

```
python -m sprigconfig.cli …
```

It returns:

```
(rc, stdout, stderr)
```

where:

- `rc` → process exit code  
- `stdout` → main CLI output  
- `stderr` → error messages  

This isolates tests from the Python environment and replicates real command‑line
usage.

---

# 📝 3. Test: `test_cli_dump_basic`

This test validates the most basic CLI behavior:

### Steps:
1. Write a minimal `application.yml` containing:
   ```yaml
   app:
     name: test-app
   ```

2. Run:
   ```
   sprigconfig dump --config-dir <tmp> --profile dev
   ```

3. Assert that:
   - Exit code is `0`  
   - Output contains `app:`  
   - Output contains `name: test-app`  

### What this confirms:
- CLI loads configuration correctly.  
- It prints merged config to stdout.  
- Basic YAML formatting is intact.  

This is a fundamental smoke test for the CLI’s “dump to stdout” mode.

---

# 📝 4. Test: `test_cli_output_file`

This test ensures that the CLI can write merged config to a file using:

```
--output out.yml
```

### Steps:
1. Write:
   ```yaml
   app:
     y: 2
   ```

2. Invoke the CLI with `--output`.

3. Assertions:
   - Exit code is `0`  
   - Output file exists  
   - File contains `y: 2`  

### Why this matters:
This verifies the CLI’s ability to:

- Produce correct merged YAML  
- Handle file output safely  
- Not pollute stdout  

This is critical for scripting, CI automation, and tooling.

---

# ✔️ Summary

These CLI tests ensure:

| Feature | Verified |
|--------|----------|
| Subprocess execution | ✔️ |
| Clean stdout (no logging noise) | ✔️ |
| Correct loading and dumping of YAML | ✔️ |
| Ability to redirect merged output to a file | ✔️ |
| CLI exit codes reflect success or failure | ✔️ |

Together, they provide **real-world validation** of the SprigConfig command‑line
interface in exactly the way end users invoke it.




---

# File: sprig-config-module/tests/test_config.md

# Documentation for `tests/test_config.py`

This document explains the purpose, design goals, and expected behavior defined
by the tests in:

```
tests/test_config.py
```

These tests collectively define the **specification** for the future
`Config` class — the object returned by both `ConfigLoader` and
`load_config()`.  
They represent a **contract**, ensuring stability, clarity, and correctness in
SprigConfig’s configuration representation.

The Markdown file corresponds directly to:

```
tests/test_config.md
```

---

# 🎯 Purpose of This Test Suite

`Config` is intended to be:

- A **read-only Mapping**
- A wrapper around nested dicts  
- Capable of **dotted-key lookup**
- Able to serialize cleanly via `to_dict()` and `dump()`
- Safe by default in how it handles `LazySecret`
- Fully backward compatible with dict-style access (`cfg["key"]`, iteration, etc.)

This test suite is a **blueprint for the implementation**.  
If a behavior is expressed here, the final `Config` class MUST adhere to it.

---

# 🧱 1. Basic Construction Tests

## `test_config_wraps_dicts_recursively`

Ensures:

- Constructing `Config(data)` wraps all nested dicts automatically.
- `cfg["a"]["b"]["c"]` behaves naturally.
- Shallow values remain unchanged.

**Why:**  
Users should be able to descend into config structures without switching types.

---

## `test_config_is_mapping_like`

Validates the Mapping API:

- `keys()`
- `items()`
- Iteration
- Membership testing (`"a" in cfg`)

**Why:**  
The `Config` object must behave like a Python mapping to support existing code.

---

# 🔍 2. Dotted-Key Access

## `test_dotted_key_access`

Ensures:

- `cfg.get("etl.jobs.root")` resolves deeply nested values.
- Partial dotted access (e.g., `"etl.jobs"`) returns either:
  - the raw underlying dict  
  - *or* a `Config` wrapper  

**Why:**  
Dotted-key lookup is one of SprigConfig’s major user-facing conveniences.

---

## `test_dotted_key_missing_returns_default`

Ensures:

- Missing dotted paths return `default` when provided.
- When no default is given, return `None`.

**Why:**  
Makes dotted-key access safe and ergonomic.

---

## `test_dotted_key_nesting_does_not_modify_data`

Verifies:

- Lookup must NOT mutate underlying data structures.

**Why:**  
Protects consumers who rely on immutability and deep copies.

---

# 🧭 3. Nested Access (Dict-Like)

## `test_nested_access_returns_config`

Ensures `cfg["a"]` returns a `Config` when the value is a nested dict.

---

## `test_nested_missing_key_raises_keyerror`

Ensures:

- `cfg["missing"]` raises `KeyError`, mirroring dict semantics.

---

# 📤 4. `to_dict()` Behavior

## `test_to_dict_returns_plain_dict`

Ensures:

- Returns a **deep copy**, not the original dict.
- Fully expands nested `Config` wrappers into raw dicts.

---

## `test_to_dict_recursively_converts_nested_config`

Ensures:

- Any nested `Config` instances are recursively converted back to dicts.

**Why:**  
Serialization functions depend on this.

---

# 📄 5. `dump()` Behavior

## `test_config_dump_writes_yaml`

Verifies:

- `cfg.dump(path)` writes a valid YAML file.
- Output YAML matches the underlying data.

---

# 🔒 6. Secret Redaction & Exposure Rules

## `test_config_to_dict_redacts_lazysecret`

Ensures:

- When converting to a plain dict,
- `LazySecret` is replaced by the placeholder:

```
<LazySecret>
```

**Why:**  
Never expose secrets by default.

---

## `test_config_dump_redacts_lazysecret`

Ensures:

- YAML dump redacts secrets (`safe=True`).

---

## `test_config_dump_can_output_plaintext_secrets`

Uses monkeypatching to override `LazySecret.get()`.

Ensures:

- `dump(..., safe=False)` outputs decrypted secrets.

**Why:**  
Accessible only when explicitly requested.

---

## `test_config_dump_raises_if_cannot_reveal_secret`

Ensures:

- Attempting `safe=False` when no key is available raises `ConfigLoadError`.

**Why:**  
Fail fast rather than silently omitting secrets.

---

# 🧪 Summary

These tests define the **intended public interface** of the `Config` object.

| Feature | Required Behavior |
|--------|-------------------|
| Mapping-like behavior | ✔️ |
| Recursive wrapping | ✔️ |
| Dotted-key access | ✔️ |
| Default handling | ✔️ |
| No mutation during access | ✔️ |
| `to_dict()` deep-copy semantics | ✔️ |
| YAML dumping | ✔️ |
| Secret redaction | ✔️ |
| Secret exposure rules | ✔️ |

The suite ensures the `Config` class is intuitive, safe, consistent, and powerful.

---

If you'd like, I can also generate a **developer README** describing how to implement `Config` to satisfy this test suite.




---

# File: sprig-config-module/tests/test_config_singleton.md

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




---

# File: sprig-config-module/tests/test_deep_merge.md

# Documentation for `tests/test_deep_merge.py`

This document describes the purpose and required behavior outlined in the test suite:

```
tests/test_deep_merge.py
```

These tests establish the **exact contract** for SprigConfig’s deep-merge implementation and how `ConfigLoader` must process:

- base config  
- profile overlays  
- literal imports  
- nested imports  
- misaligned structures  
- list replacement rules  
- circular detection  
- dotted-key access after merge  
- suppression flags  

This file defines the authoritative reference for correct deep-merge behavior in SprigConfig.

Corresponding Markdown file:

```
tests/test_deep_merge.md
```

---

# 🎯 High-Level Purpose

Deep merge behavior sits at the core of SprigConfig’s architecture.  
It determines how multiple configuration layers combine into a final, coherent, deterministic tree.

This test suite enforces:

- **Deterministic merge ordering**  
- **Structural preservation**  
- **Import semantics**  
- **Error handling**  
- **Backward compatibility**  

These rules ensure predictable behavior across complex configuration hierarchies.

---

# 🧱 1. Test Fixture

## `config_dir(use_real_config_dir)`

Provides the real directory:

```
tests/config/
```

All merge tests rely on realistic, multi-file config trees.

---

# 🔍 2. Basic Deep Merge Rules

## `test_deep_merge_root_imports`

Confirms the correct merge precedence:

```
base < profile < imports (in order)
```

Verifies:

- job-default.yml merged under `etl.jobs`
- common.yml populates additional keys
- profile overrides values (e.g., `app.debug_mode = true`)

---

## `test_deep_merge_profile_override`

Profile must override base values *deeply*, not at the top level.  
Example:

```
base.app.name → overridden by profile
base.app.debug_mode → overridden
```

---

# 📦 3. Misaligned Structures

## `test_misaligned_import_structure_kept_as_is`

Ensures:

- If a nested key imports unrelated root-level YAML, it must be inserted *as-is* beneath the calling node.
- No “structural fixups” are allowed.

This guarantees imports behave predictably regardless of shape.

---

# 🌲 4. Nested Import Behavior

## `test_nested_import_creates_nested_trees`

When a YAML file contains imports that redefine its own subtree, the result must be nested under the calling node:

```
etl.jobs    # from profile
  etl.jobs  # imported nested.yml
    foo: bar
```

Tests enforce the exact path:

```
etl.jobs.etl.jobs.foo == "bar"
```

This demonstrates SprigConfig’s **placement-before-merge** philosophy.

---

# 📝 5. List Merge Rules

## `test_lists_overwrite_not_append`

List behavior:

- Lists **overwrite**, never append.
- This prevents silent, unexpected expansions of list values.

Example:

```
prior: ["one", "two"]
import: ["three"]
→ result: ["three"]
```

---

# 🔗 6. Recursive Import Chains

## `test_recursive_import_chain`

Example chain:

```
chain1.yml → chain2.yml → chain3.yml
```

Merge order **must** follow:

```
base < profile < chain1 < chain2 < chain3
```

This verifies that imports are processed:

- in order
- one at a time
- fully resolved before being merged upward

---

# 🚫 7. Circular Import Detection

## `test_circular_import_detection`

Ensures:

- Circular references such as `a → b → a` raise `ConfigLoadError`
- Detection happens early and deterministically

This protects users from infinite recursion and obscure failures.

---

# 🎯 8. Dotted-Key Access After Merge

## `test_dotted_key_access_after_merge`

Ensures:

- After merging all layers, the `Config` object supports dotted-key lookup
- Merged nested values are accessible via `cfg.get("a.b.c")`

---

# 🔕 9. Merge Warning Suppression

## `test_merge_warning_suppression_flag`

When:

```
suppress_config_merge_warnings = true
```

Merge warnings should be suppressed throughout the entire pipeline.

The test only confirms the flag survives, but implementation must ensure:

- logging suppression  
- correct propagation  

---

# 🧩 10. Multi-Layer Interplay

## `test_merge_profile_import_interplay`

This tests a realistic scenario:

- Base defines `app.name`
- Profile overrides `app.debug_mode`
- job-default.yml fills `etl.jobs.*`

Result must honor all precedence layers.

---

# 🔙 11. Backward Compatibility: Raw Dict Merge

## `test_deep_merge_function_still_supports_dicts`

Deep merge must still support:

```python
deep_merge(dict1, dict2)
```

Meaning:

- SprigConfig’s merge engine remains usable as a standalone helper
- Existing consumers are not broken by internal changes

---

# ✔️ Summary

The deep-merge test suite defines a strict and comprehensive merging model:

| Feature | Required Behavior |
|--------|-------------------|
| Recursive merge | ✔️ |
| Strict precedence rules | ✔️ |
| Import order matters | ✔️ |
| Nested imports preserved exactly | ✔️ |
| Lists overwrite | ✔️ |
| Circular import detection | ✔️ |
| Dotted-key access after merge | ✔️ |
| Warning suppression flag | ✔️ |
| Raw dict merge backward compatibility | ✔️ |

These tests collectively enforce a predictable, powerful, and safe merging system—central to the SprigConfig architecture.

---

If you want, I can now generate:

- an **implementation guide** describing how to build deep_merge and import resolution to satisfy these tests  
- a **visual diagram** showing merge order and nesting  
- a **design doc** for the future ConfigLoader merging engine




---

# File: sprig-config-module/tests/test_full_merge_provenance.md

# tests/test_full_merge_provenance.py — Documentation

This integration test validates **SprigConfig’s full merge provenance** — confirming
that the configuration engine merges all expected files, respects import order,
applies profile overlays correctly, and produces truthful metadata in `_meta`.

---

## Purpose

To ensure that `ConfigLoader` not only merges configurations correctly but that
the resulting `_meta` information (sources, import order, and profile) **accurately
reflects the merge process**.

This is the highest‑level test in the suite: it exercises `ConfigLoader` across
real files and real merge paths, providing end‑to‑end validation of SprigConfig’s
core behavioral contract.

---

## Test Name

```
test_full_merge_provenance
```

### Location

```
tests/test_full_merge_provenance.py
```

---

## Behavior Verified

| Category | Guarantee | Description |
|-----------|------------|--------------|
| **Meta completeness** | ✅ `_meta.sources` includes every file loaded | Ensures that all base, import, and profile files appear in metadata |
| **Meta correctness** | ✅ Each `_meta` source actually exists on disk | Protects against stale or missing entries |
| **Import order** | ✅ `_meta.import_trace` respects file precedence | Validates deterministic merge order |
| **Overlay behavior** | ✅ Profile overlays override base values | Confirms profile-specific behavior (e.g., `application-dev.yml`) |
| **Additive merges** | ✅ Lists and maps merge correctly | Verifies additive semantics rather than destructive overwrites |
| **Key preservation** | ✅ Base keys persist unless explicitly overridden | Ensures no unexpected data loss |
| **Profile truthfulness** | ✅ `_meta.profile` matches active profile | Confirms provenance metadata integrity |

---

## Test Design

### 1️⃣ Setup

The test uses real files under `tests/config/`, including:

- `application.yml` (base configuration)
- `application-dev.yml` (profile overlay)
- `imports/common.yml` (imported values)

These files contain nested maps, lists, and overlays representative of typical
SprigConfig usage.

### 2️⃣ Execution

```python
loader = ConfigLoader(config_dir="tests/config", profile="dev")
config = loader.load()
meta = config["_meta"]
```

The loader processes all files, recursively following imports and overlays.

### 3️⃣ Assertions

| Step | Purpose |
|------|----------|
| `_meta.sources` contains all expected files | Verifies full provenance |
| `_meta.import_trace` ordering is correct | Ensures deterministic merge sequence |
| Overlays override base keys | Confirms correct profile behavior |
| Additive merges succeed | Ensures list/dict merges behave correctly |
| `_meta.profile` matches `"dev"` | Confirms metadata consistency |

### 4️⃣ Sanity & Integrity Checks

The test also verifies:

- Each file in `_meta.sources` exists on disk
- Nothing essential (like `app` or `metadata`) disappears during merge
- `_meta` fields (`profile`, `sources`, `import_trace`) are all present

---

## Example Success Output

```
✅ Full merge provenance verified successfully.
```

---

## Why This Test Matters

SprigConfig’s merging engine is the **core feature** of the library.
This test proves that:

- Merges are deterministic  
- Imports are traceable  
- Profiles apply predictably  
- Metadata is trustworthy  

It provides the single strongest assurance that SprigConfig behaves consistently
across environments, which is essential for stable CI/CD pipelines and 1.0.0‑level
confidence.

---

## Relationship to Other Tests

| File | Role |
|------|------|
| `test_deep_merge.py` | Verifies low‑level merge semantics |
| `test_import_trace.py` | Verifies import path recording |
| `test_profiles.py` | Verifies profile overlays individually |
| **`test_full_merge_provenance.py`** | Combines all of the above to validate holistic behavior |

---

## Future Enhancements

- Validate `_meta.import_trace` against generated `Config.sources`
- Add diff visualization for import layering (future `--trace` CLI mode)
- Extend test to include `LazySecret` behavior in merged context
- Consider a `ConfigIntegrityReport` helper for automated provenance checks

---

Generated documentation for `tests/test_full_merge_provenance.py`.



---

# File: sprig-config-module/tests/test_import_trace.md

# Documentation for `tests/test_import_trace.py`

This document explains the purpose and expected behavior defined by the import-trace test suite.  
These tests validate the **import tracing** feature within the SprigConfig configuration-loading engine.

This suite corresponds to:

```
tests/test_import_trace.md
```

---

# 🎯 Purpose of Import Trace Tests

SprigConfig must provide complete visibility into **how configuration files are loaded**, especially when `imports:` directives are used.  

To support debugging, analysis, and deterministic loading, SprigConfig records metadata under:

```
sprigconfig._meta.import_trace
sprigconfig._meta.sources
```

The tests in this file verify that:

- Every imported file is included in the trace  
- Each entry contains structural metadata  
- Depth and order are correct  
- Direct imports are attributed to the correct parent file  
- The trace order matches the `sources[]` list  
- The literal `import_key` values from YAML are preserved  

This ensures SprigConfig users can fully reconstruct the import tree.

---

# 📦 Helper: `_load_import_list()`

Loads a YAML file and extracts the raw `imports:` list.  
Used to validate that the import trace matches literal YAML content.

---

# 🧪 Test-by-Test Breakdown

---

## 1. `test_import_trace_structure`

Ensures every `import_trace` entry contains:

- `file`: Absolute file path  
- `imported_by`: Parent importer (or `None` for root)  
- `import_key`: Literal YAML value  
- `depth`: Integer nesting depth  
- `order`: Monotonic load order  

Guarantees the structure and schema of import-trace nodes.

---

## 2. `test_import_trace_direct_imports`

Validates **top-level imports**:

```
application.yml
  -> imports/job-default
  -> imports/common
```

**Note**: Import keys are now **extension-less** for format portability. The `import_key` in the trace matches the literal value from the config file (e.g., `"imports/common"`), while the `file` field contains the resolved path with extension (e.g., `"/path/to/imports/common.yml"`).

Each direct import must:

- appear in `import_trace`
- have `imported_by == application.yml`
- have `import_key` matching the literal (extension-less) value from the config
- have `file` path with the appropriate extension appended

Ensures exact, literal propagation of import directives while supporting format-agnostic imports.

---

## 3. `test_import_trace_nested_imports`

Even though the real config set contains **no nested imports**, this test verifies:

- job-default.yml and common.yml both have `imported_by == root`
- their depth equals `root.depth + 1`

This confirms direct children have identical structural placement.

---

## 4. `test_import_trace_preserves_order`

Ensures:

```
entry.order = 0, 1, 2, 3…
```

The test enforces strict monotonic ordering.  

This is vital for reproducibility and matching merge order.

---

## 5. `test_sources_and_import_trace_align`

The `sources[]` metadata must list files in the **exact same order** as import_trace, sorted by `order`.

Validates that:

```python
sources == [e["file"] for e in ordered_import_trace]
```

This creates a stable mapping between load order and import structure.

---

## 6. `test_import_trace_import_key`

Ensures the `import_key` stored in the trace is **exactly** what appeared in the config file's import list.

**Extension-less Imports**: Since v1.1.0, import keys are extension-less (e.g., `"imports/common"` instead of `"imports/common.yml"`). This allows the same configuration to work across YAML, JSON, and TOML formats without modification.

The `import_key` field preserves the literal value from the config, while the `file` field contains the fully-resolved path with the appropriate extension for the active format.

This guarantees:

- Literal preservation of user input
- Format portability (same imports work for .yml, .json, .toml)
- Debuggable import metadata
- Separation of logical imports from physical file paths  

---

# ✔️ Summary

This import-trace suite ensures SprigConfig provides complete visibility into configuration loading, supporting advanced debugging and reproducibility.

| Behavior | Required |
|---------|----------|
| Structured import metadata | ✔️ |
| Literal import key preservation | ✔️ |
| Depth and ordering guarantees | ✔️ |
| Alignment between sources[] and import_trace[] | ✔️ |
| Correct attribution of direct imports | ✔️ |
| Robustness for nested import hierarchies | ✔️ |

Together, these tests define a **clear, stable import-trace contract** that SprigConfig must follow.

---

If you'd like, I can generate:

- a visualization of the import graph  
- a merge-order timeline diagram  
- a debugging guide explaining how users interpret import_trace  




---

# File: sprig-config-module/tests/test_integration.md

# SprigConfig Full-System Integration Test Documentation

This document describes the purpose and behavior of the integration tests defined in:

```
tests/test_integration.py
```

These tests validate the complete configuration-loading pipeline of **SprigConfig RC3**, ensuring correct merging, metadata injection, secret handling, environment expansion, and backward compatibility.

---

## 🧪 Purpose of These Tests

The integration suite verifies:

- Correct merging of base + profile + imports + nested imports  
- Backward compatibility of `load_config()`  
- Accurate metadata injection under `sprigconfig._meta`  
- Proper handling and decryption of `LazySecret`  
- Environment variable expansion  
- Singleton behavior and isolation  
- Dotted-key access functionality  
- Circular import detection  
- Ability to use `APP_CONFIG_DIR` when no directory is explicitly provided  

These tests represent **end-to-end validation** of the SprigConfig system.

---

# 📝 Test-by-Test Explanation

## 1. Legacy API Support

### `test_load_config_legacy_api_still_works`
Ensures:
- `load_config()` behaves consistently with earlier versions.
- The returned object is a `Config` instance.
- Metadata such as `sprigconfig._meta.profile` is injected properly.

**Why:**  
Backward compatibility is key for dependent systems (e.g., ETL Service Web).

---

## 2. Full Merge Behavior

### `test_full_merge_dev_profile`
Validates:
- Base + profile overlays work.
- Imports and nested imports are resolved.
- Final merged values match expectations.
- Runtime profile metadata is intact.

### `test_full_merge_nested_profile`
Ensures nested import chains (imports inside imports) merge properly.

### `test_full_merge_chain_profile`
Verifies multi-step import chains (`A → B → C`) merge in order.

**Why:**  
Configuration merging is the core feature of SprigConfig—these tests prevent regressions.

---

## 3. Circular Import Detection

### `test_integration_circular_import`
Ensures circular imports raise `ConfigLoadError`.

**Why:**  
Prevents infinite recursion during config resolution.

---

## 4. Dotted-Key Access

### `test_integration_dotted_key_access`
Checks:
- Deep nested values resolve via dotted keys.
- Metadata still present.

**Why:**  
Dotted-key access is a user-facing convenience feature.

---

## 5. Environment Variable Expansion

### `test_integration_env_var_expansion`
Tests:
- `${ENV_VAR}` substitution.
- `${ENV_VAR:default}` fallback behavior.

**Why:**  
Environment-based config is essential for container deployments.

---

## 6. Secret Handling

### `test_integration_secrets_wrapped`
Validates that encrypted `ENC(...)` values are wrapped in `LazySecret`.

### `test_integration_secret_decryption`
Confirms decryption works using `APP_SECRET_KEY`.

**Why:**  
Security-sensitive functionality must never regress.

---

## 7. APP_CONFIG_DIR Default Behavior

### `test_app_config_dir_env_var`
Ensures:
- When `config_dir=None`, SprigConfig loads from `APP_CONFIG_DIR`.

**Why:**  
Required for production deployments and CLI usage.

---

## 8. Singleton Behavior

### `test_integration_singleton_independent_of_loader`
Ensures `ConfigSingleton` does not reuse `load_config()` results.

### `test_integration_singleton_dotted_keys`
Verifies:
- Singleton initialization works.
- Dotted-key access functions correctly in the singleton.

**Why:**  
The singleton is widely used in long-running services.

---

# ✔️ Summary

This test suite is **legitimate**, **high-value**, and **crucial** for guaranteeing the correctness of:

- Core merge logic  
- Environment expansion  
- Secret handling  
- Metadata injection  
- API backward compatibility  
- Import resolution  
- Singleton behavior  

Every test validates a meaningful and intentional part of SprigConfig’s design.




---

# File: sprig-config-module/tests/test_meta.md

# Documentation for `tests/test_meta.py`

This document explains the purpose, expectations, and design rules established by the metadata test suite:

```
tests/test_meta.py
```

These tests validate **runtime metadata injection** performed by `ConfigLoader`, specifically the automatic insertion of:

```
sprigconfig._meta.profile
```

This metadata key tracks the **active runtime profile** and must meet strict behavioral guarantees.

---

# 🎯 Purpose of Metadata Tests

Metadata injection is a critical feature of SprigConfig because it:

- Records the *actual* runtime profile used (`dev`, `test`, `prod`, etc.)
- Allows applications to introspect configuration state
- Must **not** interfere with user-provided configuration
- Must **not** mutate YAML trees in a way that changes business logic
- Must remain consistent regardless of overlay availability

These tests define the **contract** that `ConfigLoader` must satisfy for metadata behavior.

---

# 📂 Fixture

## `config_dir(use_real_config_dir)`

Provides:

```
tests/config/
```

as the configuration directory for all metadata tests.

---

# 🧪 Test-by-Test Breakdown

---

## 1. `test_meta_injects_runtime_profile`

Ensures that after loading:

```
cfg.get("sprigconfig._meta.profile") == profile_argument
```

This must hold **even if YAML files specify something completely different**.

### Why?
The runtime profile is a loader-level concern, not a user-configurable field.  
It must always reflect the actual entrypoint call.

---

## 2. `test_meta_profile_always_present_even_if_missing_profile_file`

Even if:

```
application-<profile>.yml
```

does **not** exist, metadata MUST still contain the runtime profile string.

Example:

```
ConfigLoader(..., profile="does_not_exist")
→ sprigconfig._meta.profile == "does_not_exist"
```

### Why?
Metadata is for runtime introspection and should not depend on overlay presence.

---

# 🔒 Non-Interference With User Config

---

## 3. `test_meta_does_not_modify_application_tree`

The loader must **not** affect normal YAML merging.

Example YAML:

```
application.yml:        app.profile = base
application-dev.yml:    app.profile = dev
```

Then:

```
app.profile → "dev"          # from YAML merge 
sprigconfig._meta.profile → "dev"   # independent metadata key
```

### Why?
Metadata is additive — it must never change or override user keys.

---

## 4. `test_meta_cannot_override_user_keys`

If a user writes:

```yaml
sprigconfig:
  _meta:
    profile: should_not_be_overwritten
```

Then SprigConfig must **NOT** overwrite it.

Instead, it must respect user-defined metadata.

### Why?
Users may supply metadata intentionally; overriding it would be destructive.

This test enforces **non-destructive metadata augmentation**.

---

# 🔍 Type Requirements

---

## 5. `test_meta_profile_is_string`

Ensures:

- Metadata profile is a **string**
- Value equals the runtime profile

This forbids accidental insertion of other types (e.g., numbers, dicts).

---

# ✔️ Summary

These tests define the rules for SprigConfig’s metadata injection system:

| Requirement | Behavior |
|------------|----------|
| Always inject runtime profile | ✔️ |
| Inject even if no profile overlay exists | ✔️ |
| **Never modify** actual YAML structures | ✔️ |
| **Never override** user-defined metadata | ✔️ |
| Store metadata as simple strings | ✔️ |
| Metadata exists in parallel to user config | ✔️ |

This suite ensures metadata is **correct**, **non-destructive**, and **predictable**, serving only as supplemental diagnostic information for the runtime.




---

# File: sprig-config-module/tests/test_meta_sources.md

# Documentation for `tests/test_meta_sources.py`

This document explains the purpose and required behavior of the metadata
**sources tracking** test suite. These tests validate how SprigConfig records the
complete list of configuration files loaded during the merge process.

The tests verify correctness of:

```
sprigconfig._meta.sources
```

This metadata field must contain a **deterministic, complete, ordered list**
of all configuration files (YAML, JSON, or TOML) that contributed to the final merged configuration.

---

# 🎯 Purpose of `sources[]`

The `sources[]` list is critical for:

- Debugging configuration merge order  
- Auditing which files influenced runtime behavior  
- Reconstructing the full config-loading sequence  
- Ensuring deterministic, testable configuration merges  
- Guaranteeing correctness of import processing  

The test ensures that:

| Requirement | Description |
|------------|-------------|
| Include all loaded config files | Base, profile, imports, nested imports (any format) |
| Preserve actual load order | Reflects deep-merge precedence |
| No missing entries allowed | Every real loaded file must appear |
| No extra entries allowed | Only actually-loaded files may appear |
| Profile-aware | Must include the profile overlay and its imports |
| Format-agnostic | Works with YAML, JSON, and TOML equally |

---

# 🧪 Helper Function: `_load_import_list(yaml_path)`

Reads a YAML file and extracts the literal `imports:` list:

```yaml
imports:
  - imports/job-default
  - imports/common
```

**Note**: Since v1.1.0, import paths are **extension-less** for format portability. The test automatically appends the correct extension (`.yml`, `.json`, or `.toml`) based on the active format when constructing expected file paths.

This lets the test automatically adjust to changes in `tests/config` without modification.

---

# 🧪 Test: `test_meta_sources_records_all_loaded_files`

This test dynamically inspects the real config tree to verify:

1. Which files should be loaded  
2. The correct merge order  
3. That `sources[]` matches reality exactly  

### **Test Steps**

---

## 1. Load Config with Full Import Tracing

```python
cfg = ConfigLoader(config_dir=full_config_dir, profile="dev").load()
sources = cfg.get("sprigconfig._meta.sources")
```

Assertions:

- `sources` must be a list  
- Must contain **at least one** entry  
- Paths are normalized to absolute paths

---

## 2. Detect Expected Files

The test extracts imports from:

- `application.yml`
- `application-dev.yml`

via:

```python
imports_base = _load_import_list(application_yml)
imports_dev  = _load_import_list(profile_yml)
```

This ensures correctness even as config files change.

---

## 3. Expected Merge Order

Expected order is:

1. `application.yml`
2. Imports from `application.yml` (in YAML list order)
3. `application-dev.yml`
4. Imports from `application-dev.yml` (in YAML list order)

This matches SprigConfig’s design:

```
base < profile < profile-imports
```

and ensures deterministic ordering.

---

## 4. Assertions

### ✔ Every expected file must appear:

```python
assert path in sources_paths
```

### ✔ No extra files may appear:

```python
assert path in expected
```

This enforces exact alignment between loader behavior and import metadata.

---

# ✔️ Summary

This test suite defines the **contract** for metadata source tracking in SprigConfig:

| Behavior | Must be True |
|----------|--------------|
| `sources[]` lists all config files actually loaded (any format) | ✔ |
| Ordering matches merge precedence | ✔ |
| No duplicates, no omissions | ✔ |
| Uses absolute resolved paths | ✔ |
| Respects extension-less import lists | ✔ |
| Profile-aware, import-aware | ✔ |
| Format-agnostic (YAML, JSON, TOML) | ✔ |

This ensures SprigConfig provides **complete, transparent, auditable** insight into all configuration sources.

---

If you'd like a combined metadata design document or import-trace diagram, I can generate that as well.



---

# File: sprig-config-module/tests/test_path_traversal.md

# test_path_traversal.py — Security Tests for Import Path Validation

## Purpose

This test module verifies that `ConfigLoader` properly protects against **path traversal attacks** in configuration imports.

Path traversal vulnerabilities occur when an attacker can use relative paths (e.g., `../../etc/passwd`) to access files outside the intended directory. This is a critical security concern for configuration systems that load files based on user-provided paths.

---

## What This Tests

### 1. **Path Traversal is Blocked** (`test_path_traversal_blocked`)

Verifies that malicious import paths are rejected:

```yaml
imports:
  - ../../etc/passwd  # ❌ Blocked!
```

**Expected Behavior**:
- `ConfigLoader` raises `ConfigLoadError` with message "Path traversal detected"
- The error message includes the offending import path and config directory
- No file is accessed outside the config directory

**Attack Scenarios Prevented**:
- Reading system files (`/etc/passwd`, `/etc/shadow`)
- Accessing parent directories (`../../../`)
- Reading sensitive application files outside config directory
- Directory traversal via symbolic links (resolved paths are validated)

### 2. **Normal Subdirectory Imports Allowed** (`test_normal_subdirectory_imports_allowed`)

Ensures that legitimate subdirectory imports still work:

```yaml
imports:
  - imports/common  # ✅ Allowed - within config_dir/imports/
```

**Expected Behavior**:
- Imports within `config_dir` and its subdirectories work normally
- Files are loaded and merged correctly
- Configuration behaves as expected

---

## Security Implementation

### Validation Logic

The `_resolve_import()` method:

1. Constructs the full path: `config_dir / import_key`
2. Resolves symlinks and relative paths: `.resolve()`
3. Validates the resolved path is within `config_dir`:
   ```python
   try:
       resolved_path.relative_to(config_dir_resolved)
   except ValueError:
       raise ConfigLoadError("Path traversal detected...")
   ```

### Why This Matters

Configuration files may come from:
- User input (uploaded configs, web forms)
- External systems (CI/CD, orchestrators)
- Untrusted sources (third-party integrations)

Without path traversal protection, a malicious configuration could:
- Read sensitive files (credentials, keys, tokens)
- Access system configuration
- Exfiltrate data from the filesystem

---

## Coverage

This test ensures:
- ✅ Upward directory traversal (`../`, `../../`) is blocked
- ✅ Absolute paths outside config_dir are blocked
- ✅ Symbolic link resolution doesn't bypass validation
- ✅ Legitimate subdirectory imports continue to work
- ✅ Error messages are clear and actionable

---

## Defense in Depth

This protection is one layer of a comprehensive security strategy:

1. **Input Validation**: Path traversal protection (this test)
2. **Least Privilege**: Run applications with minimal filesystem permissions
3. **Secret Management**: Use `LazySecret` for sensitive values (prevents logging)
4. **Immutable Config**: `Config` object discourages runtime modification

---

## Related Security Features

- `lazy_secret.py` - Encrypted secrets with deferred decryption
- `config.py` - Immutable-ish config object prevents tampering
- Production profile guards - Missing prod config raises errors

Together, these features provide robust security for production configuration management.



---

# File: sprig-config-module/tests/test_positional_import_nested_merges_in_place.md

# test_positional_import_nested_merges_in_place.md

## Purpose

This test verifies that **positional imports** inside a YAML configuration file are merged *in place* relative to where the `imports:` key appears. This ensures that SprigConfig’s import resolution preserves contextual nesting rather than flattening imported content at the root.

For example, an import nested under `etl.jobs:` results in a structure like:

```yaml
etl:
  jobs:
    imports:
      - imports/nested.yml
```

When `imports/nested.yml` defines its own `etl.jobs` section, the resulting merged tree will contain a nested structure such as:

```yaml
etl:
  jobs:
    etl:
      jobs:
        foo: bar
```

This behavior is intentional and reflects **true positional composition** — the import is merged where it was declared, not lifted or re-rooted.

---

## Test Overview

**File:** `tests/test_positional_import_nested_merges_in_place.py`

**Scenario:**
1. The base `application-nested.yml` specifies `imports:` within the `etl.jobs` section.
2. Each imported YAML file contributes configuration content that should merge at the import’s location.
3. The loader uses absolute paths and tracks the full import trace in `_meta.import_trace`.
4. The final configuration structure must show the nested merge accurately.

---

## Assertions

The test validates:

1. **Nested merge correctness:**
   - The merged config contains `etl.jobs.etl.jobs.foo == 'bar'`.
   - Nested imports do not overwrite sibling keys (`root`, `default_shell`, etc.).

2. **Import trace consistency:**
   - `_meta.import_trace` reflects each imported file in the correct order.
   - Each import has an accurate `imported_by` and `import_key`.

3. **Positional integrity:**
   - The imported content is placed exactly under the section where the import occurred.
   - No content is unexpectedly elevated to root scope.

4. **End-to-end reproducibility:**
   - Running `sprigconfig dump --config-dir=tests/config --profile=nested` produces the expected nested hierarchy.

---

## Example Output

Example snippet of the resulting merged YAML:

```yaml
etl:
  jobs:
    root: /jobs/default
    default_shell: /bin/bash
    repositories:
      inmemory:
        class: InMemoryJobRepo
        params:
          x: 1
    etl:
      jobs:
        foo: bar
    misc:
      value: 123
```

---

## Why This Matters

This test ensures SprigConfig’s import mechanism supports **deterministic hierarchical merging**, which is critical for complex configuration trees involving modular or composable YAML imports.

It protects against regressions where imports might otherwise be appended at the root or overwrite unrelated sections.

By confirming positional merge semantics, this test guarantees:

- Predictable overlay behavior
- Deterministic import graph resolution
- Safe nesting for large configuration ecosystems

---

**✅ Result:**
All assertions pass. The configuration hierarchy reflects accurate in-place import composition, with full provenance tracking.


---

# File: sprig-config-module/tests/test_profile_behavior.md

# Profile-Specific Behavior Tests (SprigConfig RC3)

This document explains the purpose and expectations of the profile‑related test suite in **tests/test_profile_behavior.py**.  
These tests validate how **SprigConfig RC3** handles base configuration, profile overlays, imports, merge order, and runtime metadata recording.

---

## ✔ What These Tests Validate

### **1. Base + Profile Merge Behavior**
Profiles modify or extend the base configuration loaded from:

- `application.yml`
- `application-<profile>.yml`

The loader must:

- Load **base first**
- Apply **profile overlays second**
- Preserve YAML field values exactly
- Store the **actual runtime profile** only in `sprigconfig._meta.profile`
- Never overwrite user keys under `app.*`

---

## ✔ 2. Profile Overrides Base Values

**Expected deep merge behavior:**

- Base fields appear in the final config.
- Profile fields override existing ones.
- New fields from profile are added.
- YAML-defined `app.profile` remains in **application tree**.

Example:

```yaml
# application.yml
app:
  name: SprigTestApp
  profile: base

# application-dev.yml
app:
  profile: dev
  debug_mode: true
```

The merge must produce:

| Key | Value |
|-----|--------|
| `app.name` | `SprigTestApp` |
| `app.profile` | `dev` *(from YAML)* |
| `app.debug_mode` | `true` |
| `sprigconfig._meta.profile` | `"dev"` *(runtime)* |

---

## ✔ 3. Missing Profile Files Must **Not** Raise Errors

If `application-<profile>.yml` is not found:

- Loader **must succeed**
- Runtime profile still recorded
- A warning is allowed, an error is not

---

## ✔ 4. Runtime Profile Must Never Be Overwritten

Even if YAML contains:

```yaml
app:
  profile: dev
```

The runtime profile passed to the loader **must only appear here**:

```text
sprigconfig._meta.profile
```

YAML values stay untouched.

---

## ✔ 5. Profile-Specific Import Chains

Some profiles trigger their own imports:

### Chain example:

```
chain1.yml → chain2.yml → chain3.yml
```

Tests ensure:

- All files load in correct order
- Merged values appear under expected keys

---

### Nested import example (`profile="nested"`):

```
application-nested.yml → nested.yml → misc.yml
```

This must produce:

```
etl.jobs.etl.jobs.foo = bar
etl.jobs.misc.value = 123
```

---

## ✔ 6. Merge Order Must Be Correct

Correct merge ordering:

1. `application.yml`  
2. `application-<profile>.yml`  
3. Imports from *base* YAML  
4. Imports from *profile* YAML  

Tests assert precedence and override semantics.

---

## ✔ 7. Suppressing Merge Warnings

If profile YAML contains:

```yaml
suppress_config_merge_warnings: true
```

Tests only assert the value is preserved; they do not capture logs.

---

## ✔ 8. Dotted-Key Access Across Profile Merges

The merged configuration must support:

```python
cfg.get("etl.jobs.repositories.inmemory.class")
cfg.get("common.feature_flag")
cfg.get("sprigconfig._meta.profile")
```

---

# Summary Table

| Behavior | Required? | Notes |
|---------|-----------|-------|
| Base loads first | ✅ | Core RC3 rule |
| Profile overlays base | ✅ | Deep-merge semantics |
| Profile adds new fields | ✅ | Additive |
| Profile-specific imports | ✅ | Must follow merge order |
| Missing profile allowed | ✅ | Must not error |
| Runtime profile stored only in metadata | ✅ | Never override YAML |
| Dotted-key access | ✅ | Must work across merged config |
| Suppress merge warnings | Optional → Preserved | Flag only |
| ConfigSingleton profile validation | Tested | Ensures correctness |

---

If you need a **full RC3 merge architecture diagram** or **API reference**, I can generate those too!




---

# File: sprig-config-module/tests/test_toml_support.md

# test_toml_support.py — TOML Format Support Tests

## Purpose

This test module verifies that `ConfigLoader` correctly supports TOML (`.toml`) configuration files alongside YAML and JSON formats.

TOML support enables users to write configurations using TOML syntax, which is particularly popular in the Python ecosystem (e.g., `pyproject.toml`).

---

## What This Tests

### 1. **Basic TOML Loading** (`test_toml_basic_loading`)

Verifies that:
- TOML files can be parsed correctly
- Nested TOML tables (e.g., `[app]`, `[server]`) are converted to Python dictionaries
- Values are accessible via dotted-key notation

### 2. **TOML with Imports** (`test_toml_with_imports`)

Tests the positional import feature with TOML files:
- Extension-less imports work (`imports = ["imports/database"]` resolves to `.toml`)
- Imported TOML content merges at the root level
- Proper structure: `imports` must be at root level in TOML (before any table headers)

**Important TOML Constraint**: Due to TOML syntax, the `imports` array must be declared at the root level before any table headers like `[app]`. This is a TOML language requirement, not a SprigConfig limitation.

### 3. **TOML Profile Overlays** (`test_toml_profile_overlay`)

Validates profile-based overrides using TOML:
- Base TOML config (`application.toml`)
- Profile overlay TOML (`application-dev.toml`)
- Deep merge semantics work correctly with TOML structures
- Profile values properly override base values

### 4. **Environment Variable Expansion** (`test_toml_env_var_expansion`)

Ensures environment variable substitution works in TOML files:
- `"${VAR}"` syntax expands to environment variable values
- `"${VAR:default}"` syntax provides fallback values
- Expansion happens before TOML parsing

---

## Why TOML Support Matters

TOML has become a standard configuration format in the Python ecosystem:
- `pyproject.toml` is the standard for Python project metadata
- TOML syntax is clean, readable, and strongly typed
- Many Python tools prefer TOML over YAML or JSON

By supporting TOML, SprigConfig allows teams to use a single configuration format across their entire Python project, from build configuration to runtime settings.

---

## Design Notes

### TOML Parsing

- Uses Python's built-in `tomllib` module (Python 3.11+)
- TOML files are read as text, environment variables are expanded, then parsed
- Parsing errors raise `ConfigLoadError` with clear messages

### Format Portability

The same import structure works across YAML, JSON, and TOML:

```toml
# application.toml
imports = ["imports/database", "imports/cache"]

[app]
name = "MyApp"
```

```yaml
# application.yml
imports:
  - imports/database
  - imports/cache

app:
  name: MyApp
```

The loader automatically resolves imports to the correct format based on the active `ext` setting.

---

## Related Tests

- `test_import_trace.py` - Verifies import tracking works across all formats
- `test_deep_merge.py` - Tests merge semantics that apply to all formats
- `test_profiles.py` - Profile overlay behavior is format-agnostic



---

# File: sprig-config-module/tests/utils/config_test_utils.md

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




---

# File: sprig-tools/README.md

# sprig-tools
Helper utilities for SprigConfig (pytest sync, requirements→TOML).



---

# File: sprig-tools/notes/format-specific-imports.md

# The AI mentioned the loader handling format specific imports.

Perfect. Here is the **direct, lossless JSON equivalent** of your `application.yml`.

No restructuring, no normalization, no “helpful” changes.

---

## `application.json`

```json
{
  "app": {
    "name": "SprigTestApp",
    "profile": "base"
  },
  "logging": {
    "level": "INFO",
    "format": "%(message)s"
  },
  "etl": {
    "jobs": {
      "root": "/jobs/default",
      "default_shell": "/bin/bash",
      "repositories": {
        "inmemory": {
          "class": "InMemoryJobRepo",
          "params": {
            "x": 1
          }
        }
      }
    }
  },
  "imports": [
    "imports/job-default.yml",
    "imports/common.yml"
  ]
}
```

---

## Parity check (important but brief)

✔ No YAML-only features used
✔ No anchors / aliases
✔ No implicit booleans
✔ No multi-line scalars
✔ Strings explicitly preserved
✔ Paths remain strings
✔ List semantics preserved

This file should produce **the exact same in-memory structure** after parsing.

---

## One subtle thing worth noting (not a blocker)

You’re already doing something *good* here:

```yaml
imports:
  - imports/job-default.yml
```

JSON doesn’t care, but **your loader might eventually** if you later support:

* format-specific imports (`.json`, `.toml`)
* or extension filtering

Right now, this is totally fine — just flagging it as a future design seam, not an issue.

---

Whenever you’re ready, paste the **next YAML file** and we’ll keep converting.

