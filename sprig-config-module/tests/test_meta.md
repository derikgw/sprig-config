# Documentation for `tests/test_meta.py`

This document explains the purpose and behaviors exercised by the metadata
test suite:

```
tests/test_meta.py
```

These tests check selected runtime-profile metadata behavior performed by
`ConfigLoader`:

```
sprigconfig._meta.profile
```

The tests assert the configured profile at this path for selected fixtures.

---

# 🎯 Purpose of Metadata Tests

These tests exercise selected runtime-profile metadata behavior:

- Records the profile passed to the loader in the tested cases
- Coexists with selected application and user metadata fixture values
- Remains available when the selected profile overlay is absent

These fixture-based tests are regression checks, not a complete specification
for every metadata field or user-provided metadata structure.

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

The test checks the `dev` fixture's loaded value.

### Why?
The runtime profile is a loader-level concern, not a user-configurable field.  
The assertion ties that value to the profile supplied in this test.

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
The tested fixture's application-tree value remains visible alongside the
runtime profile metadata.

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

This test checks the profile field for the `user-meta` fixture; it does not
establish non-overwrite behavior for every metadata key or configuration tree.

---

# 🔍 Type Requirements

---

## 5. `test_meta_profile_is_string`

Ensures:

- Metadata profile is a **string**
- Value equals the runtime profile

The assertion checks the profile value's type and value for the tested case.

---

# ✔️ Summary

These tests define the rules for SprigConfig’s metadata injection system:

| Behavior | Tested assertion |
|------------|----------|
| Always inject runtime profile | ✔️ |
| Inject even if no profile overlay exists | ✔️ |
| Selected YAML application value remains visible | ✔️ |
| Selected user `_meta.profile` fixture value is preserved | ✔️ |
| Store metadata as simple strings | ✔️ |
| Metadata exists in parallel to user config | ✔️ |

This suite uses shared YAML fixtures and asserts the profile value and selected
user-config interactions. It does not exercise every metadata field or every
possible user-provided `sprigconfig` tree.

## Run

From `sprig-config-module/`:

```bash
poetry run pytest tests/test_meta.py
```
