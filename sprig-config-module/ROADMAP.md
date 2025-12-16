# SprigConfig Roadmap (Parser Engine Focus)

## 🎯 Guiding Principles (Keep These Written Down)

- **Config behavior > file format**
- **Parsing is a leaf concern**
- **Backward compatibility is sacred in 1.x**
- **2.0 only when contracts change**

If a change violates one of these principles, it is either deferred or
explicitly reserved for a 2.0 release.

---

## ✅ Phase 1 — 1.1.0 (Completed)

**Parser Abstraction (Internal, Backward Compatible)**

> Goal: Extract parsing cleanly without changing user behavior.

### Deliverables

- Introduced an internal `ConfigParser` abstraction
- Moved YAML parsing behind the interface
- Added a parser registry (extension → parser)
- Loader delegates parsing instead of parsing directly
- All existing tests passed unchanged

### Non-Goals

- No public plugin API
- No documentation for custom parsers
- No behavior changes
- No new defaults

### Risk Level

🟢 Very Low  
This phase was primarily architectural refactoring with long-term payoff.

### Release Messaging

> “Internal refactor enabling future format extensibility. No breaking changes.”

---

## ➕ Phase 2 — 1.2.0 (Updated)

**Additional Formats (Abstraction Proven)**

> Goal: Formalize multi-format support and confirm that parsing is truly a leaf concern.

### Deliverables

- Built-in JSON parser ✅ *(validated during 1.1.x)*
- Built-in TOML parser (stdlib only)
- Explicit errors for unsupported file extensions
- Test coverage proving mixed-format layering works
- Documentation clarifying supported formats and guarantees

### Still Backward Compatible

- YAML remains the default and recommended format
- No required configuration changes
- No change in merge, import, or profile resolution semantics

### Why This Matters

This phase confirms that SprigConfig behavior is independent of file format.
The abstraction is no longer theoretical—it is exercised and proven.

### Risk Level

🟡 Low  
Edge cases (types, lists, overrides) exist, but are bounded and testable.

---

## 🧪 Phase 3 — 1.3.x

**Hardening & Provenance Improvements**

> Goal: Make mixed-format configuration debuggable, explicit, and boring.

### Deliverables

- Add `_meta.source_format` (or equivalent provenance field)
- Improve error clarity:
  - parse vs merge vs secret resolution
- Explicit documentation of merge semantics across formats
- Possibly:
  - `Config.get_source("path.to.key")`

### Still Not Yet

- No public plugin stability guarantees
- No automatic plugin discovery

This phase focuses on **operational confidence**, not new features.

---

## 🔓 Phase 4 — 1.4.x (Optional, Demand-Driven)

**Experimental Plugin Registration (Soft Public API)**

> Goal: Allow advanced users to extend parsing without promises of stability.

### Deliverables

- Public `register_parser()` function
- Clear "experimental" documentation
- Explicit statement:

  > “Parser APIs may change before 2.0”

### Why This Is Optional

If there is no demonstrated demand, this phase is skipped.
SprigConfig does not ship features for hypothetical users.

---

## 🚀 Phase 5 — 2.0.0

**Parser Engine as a First-Class Platform**

> This is the contract moment.

### What Changes in 2.0

- Parser interface is frozen and fully documented
- Plugin system is supported and versioned
- Clear guarantees around:
  - parser lifecycle
  - error behavior
  - merge expectations
- Possibly:
  - official XML support (opt-in)
  - schema hooks (still optional)

### Why This Is Worth 2.0

Because this is where SprigConfig explicitly promises:

> “You can build on this, and we won’t break you lightly.”

That is a real compatibility commitment.

---

## 📌 What You Should NOT Put on the Roadmap (Yet)

These are tempting—but dangerous:

- Automatic env-based format switching
- CLI override DSLs
- Schema validation baked into core
- Magic interpolation
- Auto-discovery of plugins

These belong in other tools, not SprigConfig core.

---

## 🧠 Strategic Insight (Important)

SprigConfig’s identity is:

> **Predictable, debuggable configuration composition.**

This roadmap reinforces that identity instead of diluting it.
You are not chasing features—you are closing a structural gap cleanly.

---

## TL;DR Roadmap Summary

| Version | Focus                    | Risk |
|--------:|--------------------------|------|
| 1.1.0   | Parser abstraction       | 🟢 |
| 1.2.0   | JSON & TOML support      | 🟡 |
| 1.3.x   | Debugging & provenance   | 🟡 |
| 1.4.x   | Experimental plugins     | 🟠 |
| 2.0.0   | Stable parser platform   | 🔴 |

