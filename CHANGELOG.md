# Changelog

All notable changes to **SprigConfig** will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [1.4.8] — 2026-04-14

### 🎯 Summary

This is a **security maintenance release** that refreshes vulnerable development dependencies used in the SprigConfig test and tooling workflow.

---

### 🔒 Security

* **Fixed CVE-2026-40192** — Updated `pillow` from `12.1.1` to `12.2.0`
* **Fixed CVE-2025-71176** — Updated `pytest` from `8.4.2` to `9.0.3`
* **Tooling compatibility refresh** — Updated `pytest-cov` from `6.2.1` to `7.1.0` to stay aligned with the refreshed pytest toolchain

---

### 🧪 Verification

* Local tests passed after refreshing the dependency set
* `pip-audit` reports `No known vulnerabilities found`

---

### 🔒 Backward Compatibility

* No runtime dependency changes
* No breaking changes to SprigConfig behavior
* No API changes
* No configuration changes required

---

## [1.4.7] — 2026-04-11

### 🎯 Summary

This is a **security patch release** that updates the `cryptography` runtime dependency to remediate `CVE-2026-39892`.

---

### 🔒 Security

* **Fixed CVE-2026-39892** — Updated `cryptography` from `46.0.6` to `46.0.7`
* **Vulnerability scope** — `cryptography` versions `45.0.0` through `46.0.6` could overflow buffers when APIs that accept Python buffers (for example, `Hash.update()`) received a non-contiguous buffer
* **Audit verification** — `pip-audit` reports `No known vulnerabilities found` after refreshing the lockfile
* **Release intent** — Keeps SprigConfig on the patched upstream release with no expected application-level behavior changes

---

### 🔒 Backward Compatibility

* No breaking changes
* No API changes
* No configuration changes required
* Existing functionality unchanged

---

## [1.4.6] — 2026-03-30

### 🎯 Summary

This is a **security maintenance release** that refreshes vulnerable dependencies and documents how to triage advisories when scanners report no vendor-confirmed fix version.

---

### 🔒 Security

* **Runtime dependency refresh** — Updated `cryptography` from `46.0.5` to `46.0.6`
* **Docs and developer tooling refresh** — Updated the resolved docs/dev dependency graph, including `requests`, `Pygments`, `mkdocs`, and `mkdocs-material`, to pull patched or newer releases
* **Audit verification** — `pip-audit` now reports `No known vulnerabilities found`

---

### 📚 Documentation Changes

* Added dependency triage guidance for advisories that have no published fix version yet
* Documented how to distinguish shipped runtime dependencies from docs/dev-only tooling exposure during security review

---

### 🔒 Backward Compatibility

* No breaking changes
* No API changes
* No configuration changes required

---

## [1.4.5] — 2026-02-23

### 🎯 Summary

This is a **bug fix and developer experience release** that corrects environment variable expansion when using an empty default value (e.g., `${VAR:}`) and adds a pre-commit hook to warn about skip-worktree files.

---

### 🛠️ Fixed

* **Empty default in env var expansion** — `${VAR:}` (colon with no value after it) was not being expanded, leaving the literal string in the config. The regex required one or more characters after the colon (`+`); changed to zero or more (`*`) so an empty default correctly resolves to `""` when the variable is unset.

---

### 🧪 Tests

* Added empty-default env var expansion tests for all three config formats:
  * `test_env_var_empty_default_expands_to_empty_string_yml` (YAML)
  * `test_env_var_empty_default_expands_to_empty_string_json` (JSON)
  * `test_toml_env_var_empty_default` (TOML)
* All tests use `monkeypatch.delenv` to guarantee the variable is absent, preventing false positives from host environment leakage

---

### ✨ Added

* **Pre-commit skip-worktree reminder** — New `skip-worktree-reminder` hook in `.pre-commit-config.yaml` that lists all files with `skip-worktree` set on every commit. This prevents developers from accidentally missing intentional changes to tracked test config files that git silently ignores.
  * Non-blocking (informational only) — prints the file list and instructions to un-skip
  * Added `scripts/check-skip-worktree.sh` helper script

---

### 🔒 Backward Compatibility

* No breaking changes
* No API changes
* No configuration changes required
* Configs using `${VAR:default}` with a non-empty default are unaffected

---

## [1.4.4] — 2026-02-11

### 🎯 Summary

This is a **security patch release** addressing a vulnerability in the cryptography dependency.

---

### 🔒 Security

* **Fixed CVE-2026-26007** — Updated `cryptography` from 46.0.1 to 46.0.5 to address security vulnerability
* **Pillow security update** — Added `pillow` 12.1.1 to dev dependencies to address vulnerability (weasyprint 68.1 did not pull in the patched version)

---

### 🔒 Backward Compatibility

* No breaking changes
* No API changes
* No configuration changes required
* Existing functionality unchanged

---

## [1.4.3] — 2026-01-31

### 🎯 Summary

This is a **documentation and developer experience release** that greatly improves error diagnostics for circular imports, adds comprehensive parser documentation, and fixes UTF-8 BOM handling for cross-platform compatibility.

---

### ✨ Added

* **Enhanced Circular Import Detection** - `config_loader.py` now shows the full cycle path in error messages:
  * Clear visualization of import chain (e.g., `a.yml -> b.yml -> c.yml -> a.yml`)
  * Makes debugging complex import graphs significantly easier
  * Error messages now include the complete cycle for faster resolution

* **Parser Module Documentation** - New comprehensive documentation files:
  * `src/sprigconfig/parsers/__init__.md` - Parser architecture overview
  * `src/sprigconfig/parsers/yaml_parser.md` - YAML parser implementation details
  * `src/sprigconfig/parsers/json_parser.md` - JSON parser implementation details
  * `src/sprigconfig/parsers/toml_parser.md` - TOML parser implementation details
  * Fully documents the internal parser abstraction layer

* **Test Documentation** - New test module guides:
  * `tests/test_injection.md` - Dependency injection test patterns
  * `tests/test_instantiate.md` - Dynamic instantiation test coverage
  * `tests/test_target_config.md` - Target configuration test strategies

---

### 🛠️ Fixed

* **UTF-8 BOM Handling** - `test_import_trace.py` and `test_meta_sources.py`:
  * Added explicit `utf-8-sig` encoding for YAML file reading
  * Prevents Windows-created files with UTF-8 BOM from causing parser issues
  * Cross-platform file compatibility significantly improved
  * Ensures consistent behavior across Windows, macOS, and Linux

---

### 📚 Documentation Changes

* **docs/index.md** - Comparison table expanded:
  * Added "Spring Python" row highlighting Spring Boot feature parity
  * Added "Dependency Injection" row comparing DI approaches
  * Added "Dynamic Instantiation" row explaining `_target_` support

* **docs/faq.md** - New Dependency Injection section:
  * Common questions about DI patterns
  * Comparison with traditional `Config.get()` approach
  * Best practices for choosing DI patterns

* **docs/getting-started.md** - Improved navigation and accuracy:
  * Added links to new features (dynamic instantiation, DI patterns)
  * Fixed relative paths for cross-document linking
  * Enhanced table of contents for better discoverability

* **Roadmaps Updated** - Both `docs/roadmap.md` and `sprig-config-module/ROADMAP.md`:
  * Updated to reflect 1.4.3 release completion
  * Clarified feature delivery timeline

---

### 🔒 Backward Compatibility

* No breaking changes
* No API changes
* No configuration changes required
* Existing functionality unchanged
* All changes are additive (documentation and improved error messages)

---

## [1.4.2] — 2026-01-26

### 🎯 Summary

This is a **security patch release** addressing a path traversal vulnerability in a transitive dependency.

---

### 🔒 Security

* **Fixed CVE-2026-23949** — Updated `jaraco-context` to 6.1.0 to address Zip Slip path traversal vulnerability in tarball extraction

---

### 🔒 Backward Compatibility

* No breaking changes
* No API changes
* No configuration changes required
* Existing functionality unchanged

---

## [1.4.1] — 2026-01-21

### 🎯 Summary

This is a **security patch release** addressing two dependency vulnerabilities with minimal production impact.

---

### 🔒 Security

* **Fixed CVE-2025-68616** — Updated `weasyprint` to 68.0 to address security vulnerability
* **Fixed CVE-2026-22701** — Updated `filelock` from 3.20.2 to 3.20.3 and `virtualenv` from 20.36.0 to 20.36.1 to address security vulnerabilities

---

### 🔄 Changed

* Removed CodeQL scanning from CI pipeline (temporarily disabled due to tooling issues)

---

### 🔒 Backward Compatibility

* No breaking changes
* No API changes
* No configuration changes required
* Existing functionality unchanged

---

## [1.4.0] — 2026-01-12

### 🎯 Summary

introducing **Hydra-style `_target_` support for dynamic class instantiation from configuration**. This enables powerful patterns like hexagonal architecture with swappable adapters instantiated directly from config files.

---

### ✨ Added

* **Dynamic Class Instantiation** - Hydra-style `_target_` support:
  * Specify a class path in config: `_target_: "my.module.ClassName"`
  * Automatically extract parameters from config section
  * Instantiate class directly from configuration
  * Perfect for hexagonal architecture and adapter patterns

* **`instantiate()` Function** - New public API in `sprigconfig`:
  * `instantiate(config_section)` - Creates instance from `_target_`
  * Automatic parameter extraction based on `__init__` signature
  * Type conversion via type hints (int, float, bool, str, list, dict)
  * `_recursive_=True` (default) - Recursively instantiate nested `_target_` objects
  * `_convert_types_=True` (default) - Apply type conversion to parameters

* **Type Conversion System**:
  * Automatic conversion based on Python type hints
  * Preserves LazySecret and Config objects (never converted)
  * Clear error messages with full context

* **Seamless @config_inject Integration**:
  * Instantiated objects work perfectly with `@config_inject` decorator
  * Constructor parameters come from `_target_` config
  * Other values still available for `@config_inject` in methods
  * Two DI patterns work together harmoniously

* **Comprehensive Documentation**:
  * Module documentation: `src/sprigconfig/instantiate.md`
  * Full API reference with examples
  * Design principles and use cases
  * Error handling and security notes

---

### 📝 Examples

**Config (YAML):**
```yaml
database:
  _target_: app.adapters.PostgresAdapter
  host: localhost
  port: 5432
  pool_size: 10
  username: ${DB_USER}
  password: ${DB_PASSWORD}
```

**Python:**
```python
from sprigconfig import ConfigSingleton, instantiate

cfg = ConfigSingleton.get()
db = instantiate(cfg.database)
# Returns: PostgresAdapter(host="localhost", port=5432, pool_size=10)
# username/password still available for @config_inject in methods
```

---

### 🧪 Testing

* 24 comprehensive tests covering all features
* **Format-agnostic testing**: Validates YAML, JSON, and TOML configs
* **Integration tests**: Verify `@config_inject` compatibility
* All tests use real config files (not inline dicts only)
* 157 total tests pass (24 new + 133 existing)

---

### 🔒 Backward Compatibility

* **No breaking changes** - Fully backward compatible
* `_target_` is just another config key if not used with `instantiate()`
* Existing code continues to work unchanged
* Opt-in feature - must explicitly call `instantiate()`

---

### 🚀 What's Next

* **1.4.0** - Feature-complete stable release
* **1.5.0+** - Future enhancements (partial support, validation framework, etc.)

---

## [1.3.0] — 2026-01-10

### 🎯 Summary

This is a **major feature release** that adds Spring Boot-style dependency injection to SprigConfig, enabling cleaner, more declarative code through descriptors and decorators.

---

### ✨ Added

* **Dependency Injection** - Three new patterns for configuration injection:
  * **`ConfigValue`** - Field-level descriptor for lazy config binding with type conversion
  * **`@ConfigurationProperties`** - Class-level decorator for auto-binding config sections
  * **`@config_inject`** - Function parameter injection decorator with override support

* **Type Conversion System**:
  * Automatic type conversion based on Python type hints (int, float, bool, str, list, dict)
  * Clear error messages with full context when conversion fails
  * Preserves LazySecret and Config objects (no conversion)

* **LazySecret Integration**:
  * Configurable `decrypt` parameter (default: False for security)
  * `decrypt=False` - Returns LazySecret object (encrypted in memory)
  * `decrypt=True` - Auto-decrypts at binding time (plaintext in memory)
  * Zero-trust security by default

* **Nested Object Binding**:
  * Auto-instantiate nested config classes recursively
  * Preserves `._config` attribute for access to underlying Config object
  * Supports multiple levels of nesting

* **Test-Only Refresh**:
  * `ConfigValue` descriptors auto-refresh after config reload (reads from new singleton)
  * `@ConfigurationProperties` instances require re-instantiation after reload
  * No production code for reload (maintains immutability guarantee)

* **Documentation**:
  * Comprehensive implementation guide: `docs/dependency-injection-explained.md`
  * Module docstrings in `src/sprigconfig/injection.py`
  * Updated README with dependency injection examples
  * Updated CLAUDE.md with dependency injection patterns

---

### 🔄 Changed

* **Public API Exports** - Added to `sprigconfig/__init__.py`:
  * `ConfigValue` - Field-level descriptor
  * `ConfigurationProperties` - Class-level decorator
  * `config_inject` - Function injection decorator

---

### 🔒 Backward Compatibility

* **No breaking changes** - 100% backward compatible
* **Config.get()** - Works exactly as before, will be supported indefinitely
* **ConfigSingleton** - No changes to initialization or access patterns
* **LazySecret** - No changes to existing secret handling
* **Dependency injection is opt-in** - Existing code requires zero changes
* **Gradual adoption** - Can mix `Config.get()` and dependency injection patterns in same codebase

---

### 📚 Examples

**Before (Traditional):**
```python
cfg = ConfigSingleton.get()
db_url = cfg.get("database.url")
db_port = cfg.get("database.port", 5432)
api_key = cfg.get("api.key").get()  # LazySecret
```

**After (Dependency Injection):**
```python
from sprigconfig import ConfigValue, ConfigurationProperties

class MyService:
    db_url: str = ConfigValue("database.url")
    db_port: int = ConfigValue("database.port", default=5432)
    api_key: str = ConfigValue("api.key", decrypt=True)

@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    url: str
    port: int
```

---

### 🎁 Benefits

* **Reduced Boilerplate** - No more repetitive `Config.get()` calls
* **Type Safety** - Automatic type conversion based on type hints
* **Security** - Zero-trust LazySecret handling (encrypted by default)
* **Clear Errors** - Rich error messages with full context
* **Testing** - Auto-refresh behavior for descriptors in tests
* **Flexibility** - Three patterns for different use cases

---

### 🔮 Future Enhancements

Potential additions for future releases (not in this version):
* Validation framework (`@Min`, `@Max`, `@Pattern`)
* Complex type hints (`list[str]`, `Optional[str]`)
* Production config reload (file watcher, hot reload)
* Nested collection binding (`list[NestedConfig]`)

---

## [1.2.5] — 2026-01-08

### 🎯 Summary

This is a **security and developer tooling release** that addresses a dependency vulnerability and adds comprehensive security scanning capabilities for both CI/CD and local development.

---

### 🔒 Security

* **Fixed CVE-2025-21441**: Updated `urllib3` from 2.6.2 to 2.6.3 to address security vulnerability

---

### ✨ Added

* **pip-audit** for dependency vulnerability scanning in GitLab CI/CD pipeline
* **Pre-commit hooks** for local security scanning:
  * pip-audit (dependency vulnerabilities) - non-blocking, informational only
  * Bandit (Python code security analysis) - runs on commits
  * ruff (linting)
* **Dependency management documentation** (`docs/dependency-management.md`) covering:
  * Viewing and understanding dependency trees
  * Finding why packages are installed (Poetry equivalent of `yarn why`)
  * Updating dependencies safely
  * Security scanning workflows
  * Vulnerability remediation procedures

---

### 🔄 Changed

* Replaced Snyk with pip-audit for dependency scanning (official PyPA tool, no authentication required)
* Added `pre-commit`, `pip-audit`, and `bandit` to dev dependencies

---

### 🔒 Backward Compatibility

* No breaking changes
* No API changes
* No configuration changes required
* Existing functionality unchanged

---

### 🧭 Notes for Developers

* Run `poetry install` to get new dev dependencies (pre-commit, pip-audit, bandit)
* Install pre-commit hooks: `poetry run pre-commit install`
* Scan dependencies manually: `poetry run pip-audit`
* Scan code manually: `poetry run bandit -r src`
* See `docs/dependency-management.md` for complete dependency management guide

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
