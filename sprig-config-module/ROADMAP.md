# SprigConfig Roadmap (Parser Engine Focus)

## 🎯 Guiding Principles (Keep These Written Down)

* **Config behavior > file format**
* **Parsing is a leaf concern**
* **Backward compatibility is sacred in 1.x**
* **2.0 only when contracts change**

If a change violates one of these, it’s either deferred or becomes 2.0.

---

## ✅ Phase 1 — 1.1.0

**Parser Abstraction (Internal, Backward Compatible)**

> Goal: Extract parsing cleanly without changing user behavior.

### Deliverables

* Introduce a `ConfigParser` interface (internal)
* Move YAML logic behind the interface
* Add parser registry (extension → parser)
* Loader delegates parsing instead of parsing directly
* All existing tests pass unchanged

### Non-Goals

* No public plugin API
* No documentation about custom parsers yet
* No behavior changes
* No new defaults

### Risk Level

🟢 Very Low
This is mostly refactoring with architectural payoff.

### Release Messaging

> “Internal refactor enabling future format extensibility. No breaking changes.”

---

## ➕ Phase 2 — 1.2.0

**First Additional Formats (Still Optional)**

> Goal: Prove the abstraction without committing to plugin stability.

### Deliverables

* Built-in JSON parser
* Built-in TOML parser (stdlib only)
* Explicit errors for unsupported extensions
* Test coverage proving mixed-format layering works

### Still Backward Compatible

* YAML remains default
* No required configuration changes

### Why This Matters

This is where the abstraction becomes *real*, not theoretical.

### Risk Level

🟡 Low
Edge cases start to appear (types, lists, overrides), but controlled.

---

## 🧪 Phase 3 — 1.3.x

**Hardening & Provenance Improvements**

> Goal: Make mixed-format configs debuggable and boring.

### Deliverables

* `_meta.source_format` (or similar)
* Improved error messages:

  * parse vs merge vs secret resolution
* Explicit documentation of merge semantics across formats
* Possibly:

  * `Config.get_source("path.to.key")`

### Still Not Yet

* No public plugin stability guarantees
* No automatic plugin discovery

This is about **operational confidence**, not features.

---

## 🔓 Phase 4 — 1.4.x (Optional, Depends on Demand)

**Experimental Plugin Registration (Soft Public API)**

> Goal: Let advanced users extend, without promises.

### Deliverables

* Public `register_parser()` function
* Clear “experimental” documentation
* Explicit statement:

  > “Parser APIs may change before 2.0”

### Why This Is Optional

If no one asks for it, you don’t ship it.
You don’t need hypothetical users.

---

## 🚀 Phase 5 — 2.0.0

**Parser Engine as a First-Class Platform**

> This is the contract moment.

### What Changes in 2.0

* Parser interface is frozen and documented
* Plugin system is supported
* Clear guarantees about:

  * parser lifecycle
  * error behavior
  * merge expectations
* Possibly:

  * official XML support (opt-in)
  * schema hooks (still optional)

### Why This Is Worth 2.0

Because now you’re saying:

> “You can build on this, and we won’t break you lightly.”

That’s a *real* promise.

---

## 📌 What You Should NOT Put on the Roadmap (Yet)

These are tempting, but dangerous:

* Automatic env-based format switching
* CLI override DSLs
* Schema validation baked into core
* Magic interpolation
* Auto-discovery of plugins

Those belong to *other libraries* — not SprigConfig.

---

## 🧠 One Strategic Insight (Important)

Right now, SprigConfig’s identity is:

> “Predictable, debuggable configuration composition.”

This roadmap **reinforces that identity** instead of diluting it.

You are not chasing features.
You are **closing a structural gap** cleanly.

---

## TL;DR Roadmap Summary

| Version | Focus                  | Risk             |
| ------- | ---------------------- | ---------------- |
| 1.1.0   | Parser abstraction     | 🟢               |
| 1.2.0   | JSON/TOML support      | 🟡               |
| 1.3.x   | Debugging & provenance | 🟡               |
| 1.4.x   | Experimental plugins   | 🟠               |
| 2.0.0   | Stable parser platform | 🔴 (intentional) |
