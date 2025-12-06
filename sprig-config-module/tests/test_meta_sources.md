# Documentation for `tests/test_meta_sources.py`

This document explains the purpose and required behavior of the metadata
**sources tracking** test suite. These tests validate how SprigConfig records the
complete list of configuration files loaded during the merge process.

The tests verify correctness of:

```
sprigconfig._meta.sources
```

This metadata field must contain a **deterministic, complete, ordered list**
of all YAML files that contributed to the final merged configuration.

---

# 🎯 Purpose of `sources[]`

The `sources[]` list is critical for:

- Debugging configuration merge order  
- Auditing which files influenced runtime behavior  
- Reconstructing the full config-loading sequence  
- Ensuring deterministic, testable configuration merges  
- Guaranteeing correctness of import processing  

The test ensures that:

| Requirement | Description |
|------------|-------------|
| Include all loaded YAML files | Base, profile, imports, nested imports |
| Preserve actual load order | Reflects deep-merge precedence |
| No missing entries allowed | Every real loaded file must appear |
| No extra entries allowed | Only actually-loaded files may appear |
| Profile-aware | Must include the profile overlay and its imports |

---

# 🧪 Helper Function: `_load_import_list(yaml_path)`

Reads a YAML file and extracts the literal `imports:` list:

```yaml
imports:
  - imports/job-default.yml
  - imports/common.yml
```

This lets the test automatically adjust to changes in `tests/config` without modification.

---

# 🧪 Test: `test_meta_sources_records_all_loaded_files`

This test dynamically inspects the real config tree to verify:

1. Which files should be loaded  
2. The correct merge order  
3. That `sources[]` matches reality exactly  

### **Test Steps**

---

## 1. Load Config with Full Import Tracing

```python
cfg = ConfigLoader(config_dir=full_config_dir, profile="dev").load()
sources = cfg.get("sprigconfig._meta.sources")
```

Assertions:

- `sources` must be a list  
- Must contain **at least one** entry  
- Paths are normalized to absolute paths

---

## 2. Detect Expected Files

The test extracts imports from:

- `application.yml`
- `application-dev.yml`

via:

```python
imports_base = _load_import_list(application_yml)
imports_dev  = _load_import_list(profile_yml)
```

This ensures correctness even as config files change.

---

## 3. Expected Merge Order

Expected order is:

1. `application.yml`
2. Imports from `application.yml` (in YAML list order)
3. `application-dev.yml`
4. Imports from `application-dev.yml` (in YAML list order)

This matches SprigConfig’s design:

```
base < profile < profile-imports
```

and ensures deterministic ordering.

---

## 4. Assertions

### ✔ Every expected file must appear:

```python
assert path in sources_paths
```

### ✔ No extra files may appear:

```python
assert path in expected
```

This enforces exact alignment between loader behavior and import metadata.

---

# ✔️ Summary

This test suite defines the **contract** for metadata source tracking in SprigConfig:

| Behavior | Must be True |
|----------|--------------|
| `sources[]` lists all YAML files actually loaded | ✔ |
| Ordering matches merge precedence | ✔ |
| No duplicates, no omissions | ✔ |
| Uses absolute resolved paths | ✔ |
| Respects real YAML import lists | ✔ |
| Profile-aware, import-aware | ✔ |

This ensures SprigConfig provides **complete, transparent, auditable** insight into all configuration sources.

---

If you'd like a combined metadata design document or import-trace diagram, I can generate that as well.
