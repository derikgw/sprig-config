---
title: SprigConfig
---

![sprig_config_logo_horizontal_150_35.svg](assets/sprig_config_logo_horizontal_150_35.svg)

# SprigConfig

**Spring Boot-style configuration management for Python.**

SprigConfig is a production-ready, lightweight configuration system that brings layered YAML configuration, runtime-driven profile selection, deep merge semantics, secure secrets handling, and complete provenance tracking to Python applications.

Think of it as **Spring Boot's configuration philosophy for Python**—but designed from the ground up for Python's simplicity and flexibility.

---

## What Is SprigConfig?

SprigConfig solves a real problem: **configuration management should be predictable, debuggable, and secure**—especially at 3am during an outage.

### Core Philosophy

✅ **Layered configuration** with deterministic deep merge semantics
✅ **Runtime-driven profiles** (dev, test, prod) that never come from files
✅ **Recursive imports** with cycle detection and provenance tracking
✅ **Encrypted secrets** that stay encrypted until you need them
✅ **Deterministic, debuggable** behavior you can reason about
✅ **Backward compatibility** is critical
✅ **Secure by default** for sensitive values

---

## Quick Start

### Installation

```bash
pip install sprig-config
```

Or with Poetry:
```bash
poetry add sprig-config
```

**Requirements:** Python 3.11 to `<4.0`

### 5-Minute Example

**Configuration files** (`config/` directory):

```yaml
# config/application.yml (base config)
server:
  port: 8080
  host: localhost
  debug: false

database:
  host: localhost
  port: 5432

logging:
  level: INFO
```

```yaml
# config/application-dev.yml (development overlay)
server:
  port: 9090      # Override base
  debug: true

logging:
  level: DEBUG    # Override base
```

**Python code:**

```python
from sprigconfig import load_config

# Load dev configuration (profile is runtime-driven)
cfg = load_config(profile="dev")

print(cfg["server.port"])      # → 9090 (from dev overlay)
print(cfg["server.host"])      # → localhost (from base)
print(cfg["server.debug"])     # → true (from dev overlay)
print(cfg["database.host"])    # → localhost (from base, not overridden)
print(cfg["app.profile"])      # → dev (injected at runtime)
```

That's it! Configuration is loaded, merged, and available via simple dotted-key access.

---

## Key Features

| Feature | What It Does |
|---------|-------------|
| **[Profile Overlays](profiles.md)** | Environment-specific config (dev, test, prod) selected at runtime |
| **[Deep Merge](merge-order.md)** | Predictable layering with collision warnings and full provenance |
| **[Recursive Imports](imports.md)** | Modular configuration with `imports:` directive and cycle detection |
| **[Secure Secrets](security.md)** | Fernet-encrypted `ENC(...)` values, decrypted on-demand with lazy evaluation |
| **[Format Support](configuration.md)** | YAML (recommended), JSON, and TOML |
| **[CLI Tools](cli.md)** | Inspect, debug, and validate merged configuration from command line |
| **[Dependency Injection](../sprig-config-module/docs/configuration-injection.md)** | `ConfigValue` descriptors, `@ConfigurationProperties`, and `@config_inject` decorators |
| **[Dynamic Instantiation](../sprig-config-module/src/sprigconfig/instantiate.md)** | Hydra-style `_target_` support for instantiating classes from config |
| **[Provenance Tracking](configuration.md#metadata)** | Know exactly where every value came from |

---

## Supported Formats

```yaml
# YAML (default, recommended)
server:
  port: 8080
```

```json
{
  "server": {
    "port": 8080
  }
}
```

```toml
[server]
port = 8080
```

All files in a single load must use the same format.

---

## Documentation Roadmap

### 🚀 I'm New to SprigConfig

Start here:
1. **[Philosophy](philosophy.md)** — Design principles and why SprigConfig exists
2. **[Getting Started](getting-started.md)** — Installation and first steps
3. **[Configuration Guide](configuration.md)** — Core concepts, API, dotted-key access
4. **[Quick Example](index.md#5-minute-example)** — See it working (you're reading it!)

### 📚 Understanding How It Works

Dive deeper into SprigConfig's behavior:
- **[Merge Order & Semantics](merge-order.md)** — Exactly how layering works
- **[Profile Overlays](profiles.md)** — Runtime-driven environment selection
- **[Recursive Imports](imports.md)** — Modular configuration with `imports:`
- **[Security & Secrets](security.md)** — Encryption, key management, best practices
- **[CLI Tools](cli.md)** — Inspect and debug configuration
- **[FAQ](faq.md)** — Common questions and troubleshooting

### 🔧 Advanced Usage

For power users and framework integration:
- **[Configuration Injection](../sprig-config-module/docs/configuration-injection.md)** — Spring Boot-style ConfigValue and @ConfigurationProperties patterns
- **[Dependency Injection Explained](../sprig-config-module/docs/dependency-injection-explained.md)** — How Spring Boot-style DI works in Python
- **[Secrets Best Practices](../sprig-config-module/docs/SprigConfig_ENC_BestPractices.md)** — Key generation, rotation, and operational security

### 👨‍💻 Contributing & Development

For developers working on SprigConfig itself:
- **[Developer Guide](../sprig-config-module/docs/README_Developer_Guide.md)** — Repository setup, testing, architecture
- **[Release Checklist](../sprig-config-module/docs/release_checklist.md)** — Releasing new versions
- **[Dependency Management](../sprig-config-module/docs/dependency-management.md)** — Managing Python dependencies with Poetry
- **[GitLab CI/CD](../sprig-config-module/docs/GitLab.md)** — CI pipeline and automated testing
- **[PyPI Publishing](../sprig-config-module/docs/PyPI.md)** — Publishing packages
- **[Building Documentation](../sprig-config-module/docs/building_documentation.md)** — Building and deploying docs

### 🔐 Operational

Guides for running SprigConfig in production:
- **[Security Guide](security.md)** — Secret management and encryption
- **[Roadmap](roadmap.md)** — Future plans and features

---

## Architecture Overview

### Configuration Loading Flow

SprigConfig follows a predictable, debuggable flow:

```
1. Profile Resolution (runtime-driven)
   ↓
   Explicit: load_config(profile="prod")
   Or: APP_PROFILE=prod environment variable
   Or: pytest context → "test"
   Or: default → "dev"

2. File Loading & Merging
   ↓
   Load application.yml (base)
   + Overlay application-<profile>.yml
   + Process recursive imports: [...]
   = Deep merge with collision warnings

3. Value Processing
   ↓
   Expand ${VAR} environment variables
   Convert ENC(...) → LazySecret objects
   Inject app.profile (runtime value)
   Inject sprigconfig._meta (provenance)

4. Return Config Object
   ↓
   Dict-like interface with dotted-key access
```

### Core Modules

Located in the SprigConfig source (`src/sprigconfig/`):

| Module | Purpose |
|--------|---------|
| `config_loader.py` | Main loading logic, merging, profile selection |
| `config.py` | Config class (dict-like interface, dotted-key access) |
| `lazy_secret.py` | LazySecret class for deferred, secure decryption |
| `deepmerge.py` | Deep merge algorithm with collision warnings |
| `injection.py` | Dependency injection (`ConfigValue`, `@ConfigurationProperties`, `@config_inject`) |
| `instantiate.py` | Dynamic class instantiation via `_target_` patterns |
| `exceptions.py` | Custom exceptions (ConfigLoadError, etc.) |
| `config_singleton.py` | Thread-safe cached loader |
| `cli.py` | Command-line interface for inspection/debugging |

---

## Design Principles

SprigConfig is built on these core principles (non-negotiable):

1. **Layered YAML** with deep merge semantics — Not just overrides, but intelligent merging
2. **Runtime-driven profile selection** — Profiles come from code/environment, never from files
3. **Deterministic, debuggable** — You can always explain where a value came from
4. **Backward compatibility** — Core behavior changes carefully, with deprecation
5. **Provenance tracking** — Full metadata about every value's origin
6. **Secure by default** — Secrets are encrypted; decryption is opt-in and explicit

---

## Use Cases

SprigConfig is ideal for:

- **Microservices** — Different configs for dev/test/staging/prod without code changes
- **12-Factor Applications** — Configuration from environment, stored securely
- **Large Applications** — Modular config with recursive imports and provenance tracking
- **Sensitive Data** — Encrypted secrets that stay encrypted until needed
- **Configuration Debugging** — Full visibility into where every value came from
- **Spring Boot Migration** — Familiar patterns for teams coming from Java/Spring

---

## Comparison

How does SprigConfig compare?

| Feature | SprigConfig | Spring Python | python-dotenv | Pydantic | hydra | pyyaml |
|---------|-------------|---------------|---------------|----------|-------|--------|
| Layered config | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Profile overlays | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Recursive imports | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Encrypted secrets | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Provenance tracking | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Multiple formats | ✅ | ✅ | ❌ | ✅ | ✅ | YAML only |
| CLI debugging | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Spring Boot style | ✅ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| Dependency injection | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Dynamic instantiation | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Validation | ⚠️ (manual) | ❌ | ❌ | ✅ | ✅ | ❌ |
| Supported Python range | `>=3.11,<4.0` | - | - | - | - | - |

**Notes on Spring Python**: Spring Python (v1.2.1) is an older project that provides IoC container and YAML/XML configuration, inspired by Spring Framework. However, it only supports Python 2.6+ (not Python 3) and lacks modern features like profile overlays, encrypted secrets, and provenance tracking. For Python developers seeking Spring-style patterns, SprigConfig offers a modern, actively-maintained alternative.

---

## Project Links

- **GitLab** (Source of truth): [gitlab.com/dgw_software/sprig-config](https://gitlab.com/dgw_software/sprig-config)
- **GitHub** (Mirror): [github.com/dgw_software/sprig-config](https://github.com/dgw_software/sprig-config)
- **PyPI** (Package): [pypi.org/project/sprigconfig](https://pypi.org/project/sprigconfig/)
- **Issues & Discussions**: [GitLab Issues](https://gitlab.com/dgw_software/sprig-config/-/issues)

---

## License

MIT License. See [LICENSE](https://gitlab.com/dgw_software/sprig-config/-/blob/main/LICENSE) for details.

---

## Getting Help

- 📖 **Documentation** — Start with [Getting Started](getting-started.md)
- ❓ **FAQ** — Check [Frequently Asked Questions](faq.md)
- 🐛 **Issues** — Report bugs or request features on [GitLab Issues](https://gitlab.com/dgw_software/sprig-config/-/issues)
- 💬 **Discussions** — Ask questions in [GitLab Discussions](https://gitlab.com/dgw_software/sprig-config/-/discussions)
- 🤝 **Contributing** — Want to help? See [Contributing Guide](../CONTRIBUTING.md)

---

**SprigConfig** — Stable. Secure. Predictable.
