# Documentation for `tests/test_meta_sources.py`

This document explains the purpose and behavior exercised by the metadata
**sources tracking** test suite. These tests validate how SprigConfig records the
source paths for the shared YAML fixture.

The tests verify correctness of:

```
sprigconfig._meta.sources
```

---

# 🎯 Purpose of `sources[]`

The test ensures that:

| Requirement | Description |
|------------|-------------|
| Include expected paths | Base, profile, and top-level imports in those YAML files |
| Reject unexpected paths | Sources match the helper's expected paths |
| Profile-aware | The YAML fixture's profile overlay is included |

---

# 🧪 Helper Function: `_load_import_list(yaml_path)`

Reads a YAML file and extracts the literal `imports:` list:

```yaml
imports:
  - imports/job-default
  - imports/common
```

**Note**: The test reads YAML and appends `.yml` to extension-less imports.

The helper reads only each file's top-level imports list. It does not recurse
through nested imported files when constructing the expected list.

---

# 🧪 Test: `test_meta_sources_records_all_loaded_files`

This test reads selected fixture files to determine:

1. Which files should be loaded  
2. The expected source paths
3. Whether those paths are present and unexpected paths are absent

### **Test Steps**

---

## 1. Load Config with Full Import Tracing

```python
cfg = ConfigLoader(config_dir=full_config_dir, profile="dev").load()
sources = cfg.get("sprigconfig._meta.sources")
```

Assertions:

- `sources` is a non-empty list
- Paths are normalized to absolute paths before comparison

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

This keeps expectations coupled to those two fixture files.

---

## 3. Expected Source Paths

The helper constructs expected paths by appending:

1. `application.yml`
2. Imports from `application.yml` (in YAML list order)
3. `application-dev.yml`
4. Imports from `application-dev.yml` (in YAML list order)

The test checks membership in both directions but does not compare order or
list length, so duplicate entries are not detected. Its helper does not recurse
through nested imports. The test also writes `config-dump.yml` to the current
working directory.

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

This test checks source membership for the current YAML fixture:

| Behavior | Assertion |
|----------|--------------|
| Expected paths are present and no unexpected paths appear | ✔ |
| Paths are normalized before comparison | ✔ |

It does not establish ordering, recursive coverage, or JSON/TOML parity.

## Run

From `sprig-config-module/`:

```bash
poetry run pytest tests/test_meta_sources.py
```
