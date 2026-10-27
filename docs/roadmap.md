---
title: Roadmap
---

# Roadmap

> This file is the canonical roadmap source for SprigConfig.
> Other roadmap files in the repository are compatibility pointers.

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

## Current Version: 1.4.13

Released: August 2026

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

### Recent Additions (1.4.9 - 1.4.13)

- **Python support expansion** (1.4.9) — Support floor moved to Python 3.11+.
- **Publishing hardening** (1.4.10) — Trusted Publishing workflow and packaging pipeline updates.
- **Security maintenance** (1.4.11, 1.4.13) — Runtime `cryptography` upgrades and dependency graph remediation.
- **Developer workflow upgrades** (1.4.12) — Committed devcontainer baseline and environment checks.

---

## Phase 5: 1.5.x

**Focus: Policy and Explainability**

### Potential Enhancements

- Configuration policy engine (guardrails as code)
  - Forbid plaintext secrets in `prod`
  - Require mandatory keys by profile/environment
  - Block risky runtime settings in production
- Explainability command (`sprigconfig explain <path>`)
  - Winning value + override chain
  - Source/provenance trail
  - Environment expansion details

---

## Phase 6: 1.6.x

**Focus: Type Contracts and Drift Detection**

### Potential Enhancements

- Typed config contracts (dataclass/Pydantic-aligned)
- Strict mode for unknown keys
- Drift detection and redacted configuration fingerprints
- Environment-to-environment effective config comparisons

---

## Phase 7: 1.7.x

**Focus: Remote Providers and Secret Lifecycle**

### Potential Enhancements

- Pluggable remote configuration providers (S3, Vault, SSM, etc.)
- Layer-preserving remote imports
- Secret rotation workflows (multi-key decrypt/re-encrypt)
- Secret age/staleness reporting

---

## Phase 8: 2.0.0

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

Remote configuration is intentionally deferred until after policy, explainability, type contracts, and drift detection are stable in 1.x.
It is planned as a later 1.x theme, not an immediate milestone.

### Hot reloading

Configuration is loaded once at startup. Hot reloading introduces complexity and potential race conditions.

### Schema validation

Dataclass schema validation is now available as an opt-in loader feature. See
[Schema Validation](schema-validation.md). Rich constraints such as ranges and
patterns remain future work.

---

## Competitive Positioning (ML and MLOps)

SprigConfig and Hydra can coexist. Hydra is optimized for experiment orchestration and sweep-heavy workflows, while SprigConfig is optimized for deterministic runtime config, secret safety, and provenance-aware operations.

### Hydra vs SprigConfig (where each excels)

| Capability | Hydra | SprigConfig | Best fit |
|---|---|---|---|
| Experiment sweeps / multirun | ✅ Excellent | ⚠️ Limited today | Hydra |
| CLI override ergonomics for run variants | ✅ Excellent | ⚠️ Basic/moderate | Hydra |
| Config composition for research workflows | ✅ Excellent | ✅ Strong | Slight Hydra edge |
| Deterministic layered merge for app/runtime config | ✅ Good | ✅✅ Strong | SprigConfig |
| Profile overlays (dev/test/prod) | ✅ Good | ✅✅ Strong | SprigConfig |
| Secret handling (encrypted config-native) | ❌ Usually external | ✅ Native | SprigConfig |
| Provenance / explainability | ⚠️ Some visibility | ✅✅ Strong focus | SprigConfig |
| Governance guardrails / policy-as-code | ⚠️ Usually custom | ✅ Planned core | SprigConfig |
| Drift and compliance operations | ⚠️ Usually custom | ✅ Planned core | SprigConfig |

### Positioning statement

Hydra optimizes experiment velocity. SprigConfig optimizes production-safe configuration governance.

---

## Release History

For complete release history and patch-level detail, see
[CHANGELOG](https://github.com/derikgw/sprig-config/blob/main/CHANGELOG.md).

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

See [CONTRIBUTING.md](https://github.com/derikgw/sprig-config/blob/main/CONTRIBUTING.md) for guidelines.

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
