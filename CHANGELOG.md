# Changelog

All notable changes to **SprigConfig** will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

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
