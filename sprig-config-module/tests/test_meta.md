# Documentation for `tests/test_meta.py`

This document explains the purpose, expectations, and design rules established by the metadata test suite:

```
tests/test_meta.py
```

These tests validate **runtime metadata injection** performed by `ConfigLoader`, specifically the automatic insertion of:

```
sprigconfig._meta.profile
```

This metadata key tracks the **active runtime profile** and must meet strict behavioral guarantees.

---

# 🎯 Purpose of Metadata Tests

Metadata injection is a critical feature of SprigConfig because it:

- Records the *actual* runtime profile used (`dev`, `test`, `prod`, etc.)
- Allows applications to introspect configuration state
- Must **not** interfere with user-provided configuration
- Must **not** mutate YAML trees in a way that changes business logic
- Must remain consistent regardless of overlay availability

These tests define the **contract** that `ConfigLoader` must satisfy for metadata behavior.

---

# 📂 Fixture

## `config_dir(use_real_config_dir)`

Provides:

```
tests/config/
```

as the configuration directory for all metadata tests.

---

# 🧪 Test-by-Test Breakdown

---

## 1. `test_meta_injects_runtime_profile`

Ensures that after loading:

```
cfg.get("sprigconfig._meta.profile") == profile_argument
```

This must hold **even if YAML files specify something completely different**.

### Why?
The runtime profile is a loader-level concern, not a user-configurable field.  
It must always reflect the actual entrypoint call.

---

## 2. `test_meta_profile_always_present_even_if_missing_profile_file`

Even if:

```
application-<profile>.yml
```

does **not** exist, metadata MUST still contain the runtime profile string.

Example:

```
ConfigLoader(..., profile="does_not_exist")
→ sprigconfig._meta.profile == "does_not_exist"
```

### Why?
Metadata is for runtime introspection and should not depend on overlay presence.

---

# 🔒 Non-Interference With User Config

---

## 3. `test_meta_does_not_modify_application_tree`

The loader must **not** affect normal YAML merging.

Example YAML:

```
application.yml:        app.profile = base
application-dev.yml:    app.profile = dev
```

Then:

```
app.profile → "dev"          # from YAML merge 
sprigconfig._meta.profile → "dev"   # independent metadata key
```

### Why?
Metadata is additive — it must never change or override user keys.

---

## 4. `test_meta_cannot_override_user_keys`

If a user writes:

```yaml
sprigconfig:
  _meta:
    profile: should_not_be_overwritten
```

Then SprigConfig must **NOT** overwrite it.

Instead, it must respect user-defined metadata.

### Why?
Users may supply metadata intentionally; overriding it would be destructive.

This test enforces **non-destructive metadata augmentation**.

---

# 🔍 Type Requirements

---

## 5. `test_meta_profile_is_string`

Ensures:

- Metadata profile is a **string**
- Value equals the runtime profile

This forbids accidental insertion of other types (e.g., numbers, dicts).

---

# ✔️ Summary

These tests define the rules for SprigConfig’s metadata injection system:

| Requirement | Behavior |
|------------|----------|
| Always inject runtime profile | ✔️ |
| Inject even if no profile overlay exists | ✔️ |
| **Never modify** actual YAML structures | ✔️ |
| **Never override** user-defined metadata | ✔️ |
| Store metadata as simple strings | ✔️ |
| Metadata exists in parallel to user config | ✔️ |

This suite ensures metadata is **correct**, **non-destructive**, and **predictable**, serving only as supplemental diagnostic information for the runtime.

