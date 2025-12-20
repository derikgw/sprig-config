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
