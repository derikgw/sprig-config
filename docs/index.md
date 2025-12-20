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
| [Profile Overlays](sprig-config/profiles.md) | Environment-specific configuration without code changes |
| [Deep Merge](sprig-config/merge-order.md) | Predictable layering with collision warnings |
| [Recursive Imports](sprig-config/imports.md) | Modular configuration with `imports:` directive |
| [Secure Secrets](sprig-config/security.md) | Fernet-encrypted values with lazy decryption |
| [CLI Tools](sprig-config/cli.md) | Inspect and debug merged configuration |
| [Provenance Tracking](sprig-config/configuration.md#metadata) | Know where every value came from |

---

## Installation

```bash
pip install sprigconfig
```

Or with Poetry:

```bash
poetry add sprigconfig
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

- [Philosophy](sprig-config/philosophy.md) — Design principles and goals
- [Getting Started](sprig-config/getting-started.md) — Installation and first steps
- [Configuration](sprig-config/configuration.md) — Core concepts and API
- [Merge Order](sprig-config/merge-order.md) — How layering works
- [Profiles](sprig-config/profiles.md) — Environment-specific overlays
- [Imports](sprig-config/imports.md) — Modular configuration
- [CLI](sprig-config/cli.md) — Command-line tools
- [Security](sprig-config/security.md) — Secret management
- [FAQ](sprig-config/faq.md) — Common questions
- [Roadmap](sprig-config/roadmap.md) — Future plans

---

## Project Links

- **Source (GitLab):** [gitlab.com/dgw_software/sprig-config](https://gitlab.com/dgw_software/sprig-config)
- **Mirror (GitHub):** [github.com/dgw_software/sprig-config](https://github.com/dgw_software/sprig-config)
- **PyPI:** [pypi.org/project/sprigconfig](https://pypi.org/project/sprigconfig/)

---

## License

MIT License. See [LICENSE](https://gitlab.com/dgw_software/sprig-config/-/blob/main/LICENSE) for details.
