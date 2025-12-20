# Documentation for `tests/test_import_trace.py`

This document explains the purpose and expected behavior defined by the import-trace test suite.  
These tests validate the **import tracing** feature within the SprigConfig configuration-loading engine.

This suite corresponds to:

```
tests/test_import_trace.md
```

---

# 🎯 Purpose of Import Trace Tests

SprigConfig must provide complete visibility into **how configuration files are loaded**, especially when `imports:` directives are used.  

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

This ensures SprigConfig users can fully reconstruct the import tree.

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

Guarantees the structure and schema of import-trace nodes.

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

Ensures exact, literal propagation of import directives while supporting format-agnostic imports.

---

## 3. `test_import_trace_nested_imports`

Even though the real config set contains **no nested imports**, this test verifies:

- job-default.yml and common.yml both have `imported_by == root`
- their depth equals `root.depth + 1`

This confirms direct children have identical structural placement.

---

## 4. `test_import_trace_preserves_order`

Ensures:

```
entry.order = 0, 1, 2, 3…
```

The test enforces strict monotonic ordering.  

This is vital for reproducibility and matching merge order.

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

This guarantees:

- Literal preservation of user input
- Format portability (same imports work for .yml, .json, .toml)
- Debuggable import metadata
- Separation of logical imports from physical file paths  

---

# ✔️ Summary

This import-trace suite ensures SprigConfig provides complete visibility into configuration loading, supporting advanced debugging and reproducibility.

| Behavior | Required |
|---------|----------|
| Structured import metadata | ✔️ |
| Literal import key preservation | ✔️ |
| Depth and ordering guarantees | ✔️ |
| Alignment between sources[] and import_trace[] | ✔️ |
| Correct attribution of direct imports | ✔️ |
| Robustness for nested import hierarchies | ✔️ |

Together, these tests define a **clear, stable import-trace contract** that SprigConfig must follow.

---

If you'd like, I can generate:

- a visualization of the import graph  
- a merge-order timeline diagram  
- a debugging guide explaining how users interpret import_trace  

