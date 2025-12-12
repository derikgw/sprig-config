# Changelog
All notable changes to **SprigConfig** will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-12-12
### Added
- End-to-end configuration loader with profile overlays and recursive imports
- Deep merge engine with circular import detection
- Secure `LazySecret` with Fernet encryption and runtime key providers
- CLI tool: `sprigconfig dump` for visualizing merged config trees
- `_meta` provenance tracking (sources + import_trace)
- Positional import resolution (nested merges)
- 100% passing test suite and CI integration

### Changed
- Promoted from RC builds (`0.2.0-rc10`) to stable release
- Refined import trace semantics and meta consistency

### Removed
- Legacy relative path merge behavior (replaced by absolute-path provenance)

---

## [Unreleased]
- CLI `--trace` and `--schema` validation options
- YAML schema integration with runtime validation
- Config audit logging
