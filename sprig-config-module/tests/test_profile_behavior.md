# Profile-Specific Behavior Tests

This document describes the tests in `tests/test_profiles.py`. They exercise
selected base/profile overlays, imports, metadata, and dotted-key access using
the repository's configuration fixtures.

---

## ✔ What These Tests Validate

### **1. Base + Profile Merge Behavior**
Profiles modify or extend the base configuration loaded from:

- `application.yml`
- `application-<profile>.yml`

The tests check selected fixture behavior:

- Base values and selected profile values appear in the merged config
- The runtime profile appears in `sprigconfig._meta.profile`
- Selected YAML-defined `app.profile` values remain in the application tree

---

## ✔ 2. Profile Overrides Base Values

The `dev` fixture test checks the following resulting values:

Example:

```yaml
# application.yml
app:
  name: SprigTestApp
  profile: base

# application-dev.yml
app:
  profile: dev
  debug_mode: true
```

The test asserts:

| Key | Value |
|-----|--------|
| `app.name` | `SprigTestApp` |
| `app.profile` | `dev` *(from YAML)* |
| `app.debug_mode` | `true` |
| `sprigconfig._meta.profile` | `"dev"` *(runtime)* |

---

## ✔ 3. Missing Profile File Case

If `application-<profile>.yml` is not found:

- Loading succeeds for the tested missing-profile name.
- The supplied profile name appears in metadata.

---

## ✔ 4. Runtime Profile Metadata

Even if YAML contains:

```yaml
app:
  profile: dev
```

The test checks that the runtime profile passed to the loader appears here:

```text
sprigconfig._meta.profile
```

The tests also check selected YAML values in the application tree; they do not
cover every possible YAML value or metadata collision.

---

## ✔ 5. Profile-Specific Import Chains

Some profiles trigger their own imports:

### Chain example:

```
chain1.yml → chain2.yml → chain3.yml
```

The tests check:

- Selected values from the fixture chain appear under expected keys

---

### Nested import example (`profile="nested"`):

```
application-nested.yml → nested.yml → misc.yml
```

This must produce:

```
etl.jobs.etl.jobs.foo = bar
etl.jobs.misc.value = 123
```

---

## ✔ 6. Selected Values for the Merge-Order Case

`test_profile_then_import_order` checks `app.debug_mode`, `common.feature_flag`,
and `etl.jobs.root`. These resulting values do not independently establish a
complete source order because the test does not compare conflicting values or
inspect a full source trace.

---

## ✔ 7. Suppressing Merge Warnings

If profile YAML contains:

```yaml
suppress_config_merge_warnings: true
```

Tests only assert the value is preserved; they do not capture logs.

---

## ✔ 8. Dotted-Key Access Across Profile Merges

The test checks dotted-key access for:

```python
cfg.get("etl.jobs.repositories.inmemory.class")
cfg.get("common.feature_flag")
cfg.get("sprigconfig._meta.profile")
```

---

# Summary Table

| Behavior | Tested? | Notes |
|---------|-----------|-------|
| Base and selected profile values appear | ✅ | Fixed `dev` fixture |
| Profile adds selected fields | ✅ | Fixed `dev` fixture |
| Profile-specific imports | ✅ | Selected result values are asserted |
| Missing profile accepted | ✅ | One missing-profile name |
| Runtime profile recorded in metadata | ✅ | Selected fixture profiles |
| Dotted-key access | ✅ | Selected merged keys |
| Suppress merge warnings | ✅ | Flag value only; no log capture |
| Missing profile rejected by singleton | ✅ | One `None` profile case |

---

## Evidence limits

The suite uses named fixture profiles (`dev`, `chain`, `nested`, `prod`,
`suppress`) and checks selected values. It does not validate all possible
profile strings, path containment, or every precedence relationship. In
particular, the order test checks output values rather than inspecting
`_meta.import_trace`.

## Run

From `sprig-config-module/`:

```bash
poetry run pytest tests/test_profiles.py
```
