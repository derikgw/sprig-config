# SprigConfig Roadmap (Parser Engine Focus)

## Guiding Principles

- Config behavior is more important than file format
- Parsing is treated as a leaf concern
- Backward compatibility is preserved throughout 1.x
- A 2.0 release occurs only when public contracts change

Any change that violates these principles is deferred or reserved for a 2.0 release.

---

## Phase 1 — 1.1.0 (Completed)

**Parser Abstraction (Internal, Backward Compatible)**

### Scope

- Internal `ConfigParser` abstraction introduced
- YAML parsing moved behind the abstraction
- Parser registry added (extension to parser)
- Loader delegates parsing instead of parsing directly
- All existing tests pass unchanged

### Non-Goals

- No public parser or plugin API
- No documentation for custom parsers
- No behavior changes
- No new defaults

---

## Phase 2 — 1.2.0

**Additional Formats**

### Scope

- Built-in JSON parser
- Built-in TOML parser (stdlib only)
- Explicit errors for unsupported file extensions
- Test coverage demonstrating mixed-format imports
- Documentation updated to reflect supported formats

### Compatibility

- YAML remains the default and recommended format
- No required configuration changes
- Merge, import, profile, and secret behavior unchanged

---

## Phase 3 — 1.3.0 (Completed)

**Dependency Injection**

### Scope

- Spring Boot-style dependency injection patterns
- `ConfigValue` descriptor for field-level lazy binding
- `@ConfigurationProperties` decorator for class-level binding
- `@config_inject` decorator for function parameter injection
- Type conversion system based on type hints
- LazySecret integration with configurable decryption
- Nested object auto-binding
- Comprehensive documentation and test coverage

### Delivered

- Three dependency injection patterns fully implemented
- 100% backward compatible (opt-in feature)
- 82% test coverage with 51 comprehensive tests
- Implementation guide: `docs/dependency-injection-explained.md`

---

## Phase 4 — 1.4.x (Planned)

**Hardening and Provenance Improvements**

### Scope

- Record source format metadata for loaded values
- Improve error clarity (parse vs merge vs secret resolution)
- Document merge semantics across formats

### Potential Enhancements

- Programmatic access to value source information
- Validation framework for dependency injection (`@Min`, `@Max`, `@Pattern`)
- Complex type hint support (`list[str]`, `Optional[str]`)

### Exclusions

- No public plugin stability guarantees
- No automatic plugin discovery

---

## Phase 5 — 1.5.x (Optional)

**Experimental Parser Registration**

### Scope

- Public `register_parser()` API
- Experimental documentation and warnings
- Explicit notice that parser APIs may change prior to 2.0

This phase is dependent on demonstrated user demand.

---

## Phase 6 — 2.0.0

**Stable Parser Platform**

### Scope

- Parser interfaces frozen and documented
- Supported plugin system with versioning guarantees
- Defined expectations for:
  - parser lifecycle
  - error behavior
  - merge semantics

### Potential Enhancements

- Optional XML support
- Optional schema integration hooks
