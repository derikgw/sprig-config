# Profile-Specific Behavior Tests (SprigConfig RC3)

This document explains the purpose and expectations of the profile‑related test suite in **tests/test_profile_behavior.py**.  
These tests validate how **SprigConfig RC3** handles base configuration, profile overlays, imports, merge order, and runtime metadata recording.

---

## ✔ What These Tests Validate

### **1. Base + Profile Merge Behavior**
Profiles modify or extend the base configuration loaded from:

- `application.yml`
- `application-<profile>.yml`

The loader must:

- Load **base first**
- Apply **profile overlays second**
- Preserve YAML field values exactly
- Store the **actual runtime profile** only in `sprigconfig._meta.profile`
- Never overwrite user keys under `app.*`

---

## ✔ 2. Profile Overrides Base Values

**Expected deep merge behavior:**

- Base fields appear in the final config.
- Profile fields override existing ones.
- New fields from profile are added.
- YAML-defined `app.profile` remains in **application tree**.

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

The merge must produce:

| Key | Value |
|-----|--------|
| `app.name` | `SprigTestApp` |
| `app.profile` | `dev` *(from YAML)* |
| `app.debug_mode` | `true` |
| `sprigconfig._meta.profile` | `"dev"` *(runtime)* |

---

## ✔ 3. Missing Profile Files Must **Not** Raise Errors

If `application-<profile>.yml` is not found:

- Loader **must succeed**
- Runtime profile still recorded
- A warning is allowed, an error is not

---

## ✔ 4. Runtime Profile Must Never Be Overwritten

Even if YAML contains:

```yaml
app:
  profile: dev
```

The runtime profile passed to the loader **must only appear here**:

```text
sprigconfig._meta.profile
```

YAML values stay untouched.

---

## ✔ 5. Profile-Specific Import Chains

Some profiles trigger their own imports:

### Chain example:

```
chain1.yml → chain2.yml → chain3.yml
```

Tests ensure:

- All files load in correct order
- Merged values appear under expected keys

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

## ✔ 6. Merge Order Must Be Correct

Correct merge ordering:

1. `application.yml`  
2. `application-<profile>.yml`  
3. Imports from *base* YAML  
4. Imports from *profile* YAML  

Tests assert precedence and override semantics.

---

## ✔ 7. Suppressing Merge Warnings

If profile YAML contains:

```yaml
suppress_config_merge_warnings: true
```

Tests only assert the value is preserved; they do not capture logs.

---

## ✔ 8. Dotted-Key Access Across Profile Merges

The merged configuration must support:

```python
cfg.get("etl.jobs.repositories.inmemory.class")
cfg.get("common.feature_flag")
cfg.get("sprigconfig._meta.profile")
```

---

# Summary Table

| Behavior | Required? | Notes |
|---------|-----------|-------|
| Base loads first | ✅ | Core RC3 rule |
| Profile overlays base | ✅ | Deep-merge semantics |
| Profile adds new fields | ✅ | Additive |
| Profile-specific imports | ✅ | Must follow merge order |
| Missing profile allowed | ✅ | Must not error |
| Runtime profile stored only in metadata | ✅ | Never override YAML |
| Dotted-key access | ✅ | Must work across merged config |
| Suppress merge warnings | Optional → Preserved | Flag only |
| ConfigSingleton profile validation | Tested | Ensures correctness |

---

If you need a **full RC3 merge architecture diagram** or **API reference**, I can generate those too!

