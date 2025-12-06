# sprigconfig/config_loader.py — Explanation and Purpose

This document explains the purpose, design, and behavior of `ConfigLoader`, the core configuration‑loading engine for **SprigConfig**. This file is responsible for turning a directory of YAML files into a single, deeply‑merged, environment‑aware, import‑traceable configuration object.

---

## 1. What `ConfigLoader` Is For

SprigConfig aims to reproduce the power and ergonomics of Spring Boot–style configuration loading, but in Python.  
`ConfigLoader` is the component that:

- Loads the base configuration (`application.yml`)
- Applies a runtime profile overlay (`application-<profile>.yml`)
- Expands `${ENV}` variables inside YAML
- Follows recursive `imports:` statements across multiple files
- Detects circular imports
- Deep‑merges structures with clear override semantics
- Wraps encrypted values (`ENC(...)`) with `LazySecret` objects
- Adds internal metadata so applications can introspect how the configuration was built

It is the **heart of SprigConfig**, turning a folder of flexible YAML sources into a structured, immutable configuration tree.

---

## 2. Why This File Exists

Python has no native configuration loading standard as powerful as Spring Boot.  
Real systems need:

- Profiles (dev, test, prod, etc.)
- Separation between base config and overrides
- Secrets that are not eagerly decrypted
- Modular configuration via file imports
- Strong cycle detection when imports chain together
- A way to trace *exactly how* the final config was constructed  
  (e.g., for debugging CI failures or misconfigured deployments)

`ConfigLoader` solves these problems by providing:

### ✔ Predictable ordering  
Base → profile overlay → imported files in deterministic merge order.

### ✔ Safety  
Circular imports throw explicit `ConfigLoadError`.

### ✔ Transparency  
`_meta.sources` and `_meta.import_trace` reveal every file loaded, in order.

### ✔ Secret‑hygiene  
Encrypted values remain encrypted until accessed, preventing accidental logging.

### ✔ Full reproducibility  
Given the same directory and profile, the result is always identical.

---

## 3. High‑Level Flow of the Loader

### **Step 1: Load `application.yml`**

The base file is always required; it establishes the root config structure.

It is recorded as the **first** entry in the import trace.

### **Step 2: Load `application-<profile>.yml`**

If the overlay exists, it is deeply merged into the base config.

This allows profile‑specific overrides, such as:

- Different DB credentials
- Different host/port values
- Test‑specific toggles

### **Step 3: Apply recursive imports**

Any YAML node may include:

```yaml
imports:
  - common.yml
  - logging.yml
```

`ConfigLoader` resolves each file path relative to the config directory, loads it, merges it, and records it in the import history.

It tracks:

- Import depth  
- Which file imported which  
- The order files were processed  
- Circular import violations

### **Step 4: Inject the runtime profile**

Under:

```yaml
app:
  profile: <profile>
```

The application always knows what profile it is running under.

### **Step 5: Add internal metadata**

Stored under:

```yaml
sprigconfig:
  _meta:
    profile: dev
    sources: [...]
    import_trace: [...]
```

This metadata supports:

- Debugging configuration merges
- Logging the provenance of runtime settings
- Unit testing and CI verification

### **Step 6: Wrap encrypted values**

Any string matching `ENC(...)` becomes a `LazySecret`, such as:

```yaml
db:
  password: ENC(gAAAAABl...)
```

Secrets remain encrypted until explicitly decrypted, preventing accidental exposure in logs or dumps.

---

## 4. Key Internal Components

### ### `_load_yaml(path: Path)`
Reads YAML from disk, expands `${ENV}` variables, and returns a Python dictionary.

### `_expand_env(text: str)`
Substitutes `${VAR}` or `${VAR:default}` using environment variables.

### `_apply_imports_recursive(node, ...)`
Walks the entire config tree and processes `imports` wherever they appear—not just the top.

### `_inject_secrets(data)`
Turns encrypted values into `LazySecret` objects.

### `_inject_metadata(merged)`
Populates the `_meta` section with traces, sources, and profile.

---

## 5. Why Import Tracing Matters

Modern deployments depend on:

- CI/CD automation
- Per‑environment overlays
- Local developer configurations
- Encrypted secrets

When something behaves unexpectedly, you must answer:

- **Which file set this value?**
- **What order were configs merged in?**
- **Where did this secret come from?**
- **Was something overridden unexpectedly?**

The import trace gives you a timeline of the entire merge process.

---

## 6. Returned Object: `Config`

The final result of `ConfigLoader.load()` is a `Config` object, which:

- Is mapping‑like (supports `dict` operations)
- Supports dotted key lookups (`cfg.get("server.port")`)
- Maintains immutability semantics
- Provides safe `.to_dict()` and `.dump()` behavior  
  (redacting secrets unless explicitly told otherwise)

---

## 7. Summary

`ConfigLoader` exists to provide a **robust, production‑grade configuration system** for Python services.

It enables:

- Hierarchical config structure  
- Deterministic merges  
- Profile‑aware overrides  
- Secure encrypted secrets  
- Full lineage and traceability  
- Safety from circular references  
- Debuggable, testable config behavior

This file is foundational to the SprigConfig project and enables consistent, scalable configuration loading for complex Python applications.

---

