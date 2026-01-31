---
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

## Current Version: 1.4.2

Released: January 2026

### Features

- Multi-format support (YAML, JSON, TOML)
- Profile-based configuration overlays
- Recursive imports with cycle detection
- Deep merge with collision warnings
- Encrypted secrets with lazy decryption
- Complete provenance tracking
- CLI for configuration inspection
- pytest integration
- **Dependency injection** — `ConfigValue`, `@ConfigurationProperties`, `@config_inject`
- **Dynamic instantiation** — Hydra-style `_target_` support via `instantiate()`

### Recent Additions (1.3.0 - 1.4.2)

- **Dependency injection patterns** (1.3.0) — Spring Boot-style configuration injection with three patterns:
  - `ConfigValue` — Field-level descriptor for lazy config binding with type conversion
  - `@ConfigurationProperties` — Class-level decorator for auto-binding config sections
  - `@config_inject` — Function parameter injection decorator with override support
- **Dynamic class instantiation** (1.4.0) — Hydra-style `_target_` support for instantiating classes from configuration
- **Type conversion system** — Automatic conversion based on Python type hints
- **Security patches** (1.4.1, 1.4.2) — Dependency vulnerability fixes

---

## Phase 5: 1.5.x

**Focus: Validation and Enhanced Type Support**

### Potential Enhancements

- Validation framework (`@Min`, `@Max`, `@Pattern`)
- Complex type hints (`list[str]`, `Optional[str]`)
- Nested collection binding (`list[NestedConfig]`)
- Enhanced error messages for configuration binding

---

## Phase 6: 2.0.0

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

### 1.4.2 (January 2026)

- Security patch for jaraco-context CVE-2026-23949

### 1.4.1 (January 2026)

- Security patches for weasyprint and filelock vulnerabilities

### 1.4.0 (January 2026)

- Hydra-style `_target_` support for dynamic class instantiation
- `instantiate()` function for creating instances from configuration
- Type conversion based on Python type hints
- Seamless `@config_inject` integration

### 1.3.0 (January 2026)

- Spring Boot-style dependency injection patterns
- `ConfigValue` field-level descriptor
- `@ConfigurationProperties` class-level decorator
- `@config_inject` function parameter injection
- LazySecret integration with configurable decrypt behavior

### 1.2.5 (January 2026)

- Security scanning with pip-audit and Bandit
- Pre-commit hooks for local security scanning
- Dependency management documentation

### 1.2.4 (December 2025)

- Full TOML format support with feature parity

### 1.2.0 (December 2025)

- TOML configuration format support
- `--format` CLI flag
- Merge order bug fix

### 1.1.0 (December 2025)

- Format-agnostic configuration loading
- JSON configuration format support
- Internal parser abstraction

### 1.0.0 (December 2025)

- Initial stable release
- YAML-based deep-merge configuration
- Profile overlays
- Recursive imports
- Secure lazy secrets
- CLI tooling

See [CHANGELOG](https://gitlab.com/dgw_software/sprig-config/-/blob/main/CHANGELOG.md) for complete version history.

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
