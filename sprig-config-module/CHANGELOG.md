# Changelog

All notable changes to **SprigConfig** will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

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
