---
title: Philosophy
---

# Philosophy

SprigConfig is built on a set of guiding principles that inform every design decision. Understanding these principles helps you use the library effectively and predict its behavior.

---

## Core Principles

### 1. Config behavior is more important than file format

What your configuration *does* matters more than *how* it's written. SprigConfig focuses on predictable, deterministic behavior regardless of whether you use YAML, JSON, or TOML.

The merge algorithm, import resolution, and secret handling work identically across all formats. Parsing is treated as a leaf concern—a detail that shouldn't affect configuration semantics.

### 2. Parsing is a leaf concern

SprigConfig separates **configuration behavior** (merging, profiles, imports) from **file parsing**. This means:

- Adding a new format doesn't change how merging works
- Debugging focuses on configuration values, not parser quirks
- The same tests validate behavior across all formats

### 3. Backward compatibility is sacred in 1.x

Every 1.x release maintains backward compatibility with previous 1.x releases. Existing projects continue to work without changes. Breaking changes are reserved for 2.0.

### 4. 2.0 only when contracts change

A major version bump happens only when public APIs or documented behavior must change. We avoid version inflation—2.0 means something significant changed.

---

## Design Philosophy

### Explicit over implicit

Configuration behavior should be obvious from looking at the files. SprigConfig avoids magic that makes configuration hard to understand.

- Profiles are always set at runtime, never from files
- Import order is explicit in the `imports:` list
- Override collisions generate warnings

### Deterministic over convenient

Given the same inputs, SprigConfig always produces the same output. There are no race conditions, random behaviors, or order-dependent surprises.

- Merge order is documented and consistent
- Import resolution follows explicit rules
- Metadata tracks exactly what was loaded

### Traceability over minimalism

Every configuration value should be traceable to its source. SprigConfig injects metadata that tells you:

- Which files were loaded
- In what order they were merged
- What the active profile is
- The complete import graph

This makes debugging configuration issues straightforward—you can see exactly where each value came from.

### Debuggable at 3am

When something goes wrong in production, you need to understand your configuration quickly. SprigConfig is designed to make this easy:

- Clear error messages that identify the source
- CLI tools for inspecting merged configuration
- Provenance tracking in every loaded config
- Collision warnings that help catch mistakes

---

## What SprigConfig Is Not

SprigConfig is intentionally focused. It does not:

- **Validate schemas** — Use Pydantic or similar for validation
- **Manage environment variables** — Use python-dotenv or similar
- **Handle remote configuration** — It loads local files only
- **Support hot reloading** — Configuration is loaded once at startup

This focus allows SprigConfig to do its core job exceptionally well.

---

## Supported Formats

SprigConfig supports formats that **natively express hierarchical configuration**:

| Format | Supported | Reason |
|--------|-----------|--------|
| YAML | Yes | Native hierarchy, comments, readability |
| JSON | Yes | Strict, portable, tooling support |
| TOML | Yes | Modern, stdlib support in Python 3.11+ |
| INI | No | Flat format requiring invented semantics |
| Properties | No | Flat format requiring dot-splitting |

Flat formats are not supported because they would require inventing behavior for:
- Dot-splitting keys into hierarchy
- List coercion rules
- Type inference

This invented behavior would violate the principle that configuration behavior should be explicit and predictable.

---

## Contributing Considerations

When contributing to SprigConfig, keep these principles in mind:

1. **Preserve existing behavior** unless explicitly changing it
2. **Avoid format-specific logic** in core paths
3. **Include tests** that validate behavior across formats
4. **Choose clarity** over cleverness
5. **Document behavior** that affects configuration semantics

See [CONTRIBUTING.md](https://gitlab.com/dgw_software/sprig-config/-/blob/main/sprig-config-module/CONTRIBUTING.md) for detailed guidelines.

---

[← Back to Documentation](index.md)
