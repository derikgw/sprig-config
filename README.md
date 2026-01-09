# 🌱 SprigConfig Monorepo

This repository is a **monorepo** containing the core SprigConfig runtime
along with supporting tools and developer utilities.

If you are looking to *use* SprigConfig in your Python project, you almost
certainly want **`sprig-config-module`**.

---

## 📦 sprig-config-module (Primary Project)
[![PyPI version](https://img.shields.io/pypi/v/sprig-config.svg)](https://pypi.org/project/sprig-config/)
[![Security Scan](https://img.shields.io/badge/security-monitored-brightgreen)](https://sprig-config-7f4835.gitlab.io/)

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
