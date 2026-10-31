# Documentation for `tests/test_import_trace.py`

This document explains the purpose and expected behavior defined by the import-trace test suite.  
These tests check selected import-trace metadata for the repository's YAML
fixture.

The companion test module is `tests/test_import_trace.py`.

---

# 🎯 Purpose of Import Trace Tests

The loader records metadata about files loaded through `imports:`. This suite
checks selected fields and relationships in the shared fixture.

To support debugging, analysis, and deterministic loading, SprigConfig records metadata under:

```
sprigconfig._meta.import_trace
sprigconfig._meta.sources
```

The tests in this file verify that:

- Every imported file is included in the trace  
- Each entry contains structural metadata  
- Depth and order are correct  
- Direct imports are attributed to the correct parent file  
- The trace order matches the `sources[]` list  
- The literal `import_key` values from YAML are preserved  

This provides evidence for the tested fixture relationships; it is not a
general guarantee that every import graph is represented correctly.

---

# 📦 Helper: `_load_import_list()`

Loads a YAML file and extracts the raw `imports:` list.  
Used to validate that the import trace matches literal YAML content.

---

# 🧪 Test-by-Test Breakdown

---

## 1. `test_import_trace_structure`

Ensures every `import_trace` entry contains:

- `file`: Absolute file path  
- `imported_by`: Parent importer (or `None` for root)  
- `import_key`: Literal YAML value  
- `depth`: Integer nesting depth  
- `order`: Monotonic load order  

Checks required fields and integer types for entries in this fixture's trace.

---

## 2. `test_import_trace_direct_imports`

Validates **top-level imports**:

```
application.yml
  -> imports/job-default
  -> imports/common
```

**Note**: Import keys are now **extension-less** for format portability. The `import_key` in the trace matches the literal value from the config file (e.g., `"imports/common"`), while the `file` field contains the resolved path with extension (e.g., `"/path/to/imports/common.yml"`).

Each direct import must:

- appear in `import_trace`
- have `imported_by == application.yml`
- have `import_key` matching the literal (extension-less) value from the config
- have `file` path with the appropriate extension appended

Checks the direct imports defined in the YAML fixture. It does not test the
same import metadata in JSON or TOML.

---

## 3. `test_import_trace_nested_imports`

Despite its name, the current fixture has **no nested import chain**. This test
verifies that:

- job-default.yml and common.yml both have `imported_by == root`
- their depth equals `root.depth + 1`

This confirms direct children have identical structural placement.

---

## 4. `test_import_trace_preserves_order`

Ensures:

```
entry.order = 0, 1, 2, 3…
```

The test checks that `order` values are sorted; it does not assert that they
are contiguous or unique.

This checks sorted order values in the fixture, not every possible merge
ordering.

---

## 5. `test_sources_and_import_trace_align`

The `sources[]` metadata must list files in the **exact same order** as import_trace, sorted by `order`.

Validates that:

```python
sources == [e["file"] for e in ordered_import_trace]
```

This creates a stable mapping between load order and import structure.

---

## 6. `test_import_trace_import_key`

Ensures the `import_key` stored in the trace is **exactly** what appeared in the config file's import list.

**Extension-less Imports**: Since v1.1.0, import keys are extension-less (e.g., `"imports/common"` instead of `"imports/common.yml"`). This allows the same configuration to work across YAML, JSON, and TOML formats without modification.

The `import_key` field preserves the literal value from the config, while the `file` field contains the fully-resolved path with the appropriate extension for the active format.

This checks literal import-key preservation for the selected YAML fixture.

---

# ✔️ Summary

This suite provides regression evidence for the fixture's trace data, not
complete visibility for arbitrary configuration graphs.

| Behavior | Required |
|---------|----------|
| Structured import metadata | ✔️ |
| Literal import key preservation | ✔️ |
| Selected depth and sorted order values | ✔️ |
| Alignment between sources[] and import_trace[] | ✔️ |
| Correct attribution of direct imports | ✔️ |
| Robustness for nested import hierarchies | ✔️ |

## Run

From `sprig-config-module/`:

```bash
poetry run pytest tests/test_import_trace.py
```
