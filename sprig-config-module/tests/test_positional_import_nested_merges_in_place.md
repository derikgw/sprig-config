# test_positional_import_nested_merges_in_place.md

## Purpose

This test verifies that **positional imports** inside a YAML configuration file are merged *in place* relative to where the `imports:` key appears. This ensures that SprigConfig’s import resolution preserves contextual nesting rather than flattening imported content at the root.

For example, an import nested under `etl.jobs:` results in a structure like:

```yaml
etl:
  jobs:
    imports:
      - imports/nested.yml
```

When `imports/nested.yml` defines its own `etl.jobs` section, the resulting merged tree will contain a nested structure such as:

```yaml
etl:
  jobs:
    etl:
      jobs:
        foo: bar
```

This behavior is intentional and reflects **true positional composition** — the import is merged where it was declared, not lifted or re-rooted.

---

## Test Overview

**File:** `tests/test_positional_import_nested_merges_in_place.py`

**Scenario:**
1. The base `application-nested.yml` specifies `imports:` within the `etl.jobs` section.
2. Each imported YAML file contributes configuration content that should merge at the import’s location.
3. The loader uses absolute paths and tracks the full import trace in `_meta.import_trace`.
4. The final configuration structure must show the nested merge accurately.

---

## Assertions

The test validates:

1. **Nested merge correctness:**
   - The merged config contains `etl.jobs.etl.jobs.foo == 'bar'`.
   - Nested imports do not overwrite sibling keys (`root`, `default_shell`, etc.).

2. **Import trace consistency:**
   - `_meta.import_trace` reflects each imported file in the correct order.
   - Each import has an accurate `imported_by` and `import_key`.

3. **Positional integrity:**
   - The imported content is placed exactly under the section where the import occurred.
   - No content is unexpectedly elevated to root scope.

4. **End-to-end reproducibility:**
   - Running `sprigconfig dump --config-dir=tests/config --profile=nested` produces the expected nested hierarchy.

---

## Example Output

Example snippet of the resulting merged YAML:

```yaml
etl:
  jobs:
    root: /jobs/default
    default_shell: /bin/bash
    repositories:
      inmemory:
        class: InMemoryJobRepo
        params:
          x: 1
    etl:
      jobs:
        foo: bar
    misc:
      value: 123
```

---

## Why This Matters

This test ensures SprigConfig’s import mechanism supports **deterministic hierarchical merging**, which is critical for complex configuration trees involving modular or composable YAML imports.

It protects against regressions where imports might otherwise be appended at the root or overwrite unrelated sections.

By confirming positional merge semantics, this test guarantees:

- Predictable overlay behavior
- Deterministic import graph resolution
- Safe nesting for large configuration ecosystems

---

**✅ Result:**
All assertions pass. The configuration hierarchy reflects accurate in-place import composition, with full provenance tracking.