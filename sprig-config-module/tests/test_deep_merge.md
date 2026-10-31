# Documentation for `tests/test_deep_merge.py`

This document describes the purpose and behavior exercised by the test suite:

```
tests/test_deep_merge.py
```

These tests exercise representative deep-merge behavior and how `ConfigLoader`
processes:

- base config  
- profile overlays  
- literal imports  
- nested imports  
- misaligned structures  
- list replacement rules  
- circular detection  
- dotted-key access after merge  
- suppression flags  

These fixture-based checks are regression evidence for the cases below, not an
exhaustive specification for every possible configuration tree.

Corresponding Markdown file:

```
tests/test_deep_merge.md
```

---

# 🎯 High-Level Purpose

Deep merge behavior sits at the core of SprigConfig’s architecture.  
It determines how multiple configuration layers combine into a final, coherent, deterministic tree.

This test suite enforces:

- **Deterministic merge ordering**  
- **Structural preservation**  
- **Import semantics**  
- **Error handling**  
- **Backward compatibility**  

These rules ensure predictable behavior across complex configuration hierarchies.

---

# 🧱 1. Test Fixture

## `config_dir(use_real_config_dir)`

Provides the real directory:

```
tests/config/
```

All merge tests rely on realistic, multi-file config trees.

---

# 🔍 2. Basic Deep Merge Rules

## `test_deep_merge_root_imports`

Confirms the correct merge precedence:

```
base < profile < imports (in order)
```

Verifies:

- job-default.yml merged under `etl.jobs`
- common.yml populates additional keys
- profile overrides values (e.g., `app.debug_mode = true`)

---

## `test_deep_merge_profile_override`

Profile must override base values *deeply*, not at the top level.  
Example:

```
base.app.name → overridden by profile
base.app.debug_mode → overridden
```

---

# 📦 3. Misaligned Structures

## `test_misaligned_import_structure_kept_as_is`

Ensures:

- If a nested key imports unrelated root-level YAML, it must be inserted *as-is* beneath the calling node.
- No “structural fixups” are allowed.

This checks the selected nested value for this fixture; other shapes are not
covered by this assertion.

---

# 🌲 4. Nested Import Behavior

## `test_nested_import_creates_nested_trees`

When a YAML file contains imports that redefine its own subtree, the result must be nested under the calling node:

```
etl.jobs    # from profile
  etl.jobs  # imported nested.yml
    foo: bar
```

Tests enforce the exact path:

```
etl.jobs.etl.jobs.foo == "bar"
```

This demonstrates SprigConfig’s **placement-before-merge** philosophy.

---

# 📝 5. List Merge Rules

## `test_lists_overwrite_not_append`

List behavior:

- Lists **overwrite**, never append.
- This prevents silent, unexpected expansions of list values.

Example:

```
prior: ["one", "two"]
import: ["three"]
→ result: ["three"]
```

---

# 🔗 6. Recursive Import Chains

## `test_recursive_import_chain`

Example chain:

```
chain1.yml → chain2.yml → chain3.yml
```

Merge order **must** follow:

```
base < profile < chain1 < chain2 < chain3
```

This verifies that imports are processed:

- in order
- one at a time
- fully resolved before being merged upward

---

# 🚫 7. Circular Import Detection

## `test_circular_import_detection`

Ensures:

- Circular references such as `a → b → a` raise `ConfigLoadError`
- Detection happens early and deterministically

This protects users from infinite recursion and obscure failures.

---

# 🎯 8. Dotted-Key Access After Merge

## `test_dotted_key_access_after_merge`

Ensures:

- After merging all layers, the `Config` object supports dotted-key lookup
- Merged nested values are accessible via `cfg.get("a.b.c")`

---

# 🔕 9. Merge Warning Suppression

## `test_merge_warning_suppression_flag`

When:

```
suppress_config_merge_warnings = true
```

Merge warnings should be suppressed throughout the entire pipeline.

The assertion checks only that the flag survives loading. It does **not**
capture logs or establish that merge warnings were actually suppressed.

---

# 🧩 10. Multi-Layer Interplay

## `test_merge_profile_import_interplay`

This tests a realistic scenario:

- Base defines `app.name`
- Profile overrides `app.debug_mode`
- job-default.yml fills `etl.jobs.*`

Result must honor all precedence layers.

---

# 🔙 11. Backward Compatibility: Raw Dict Merge

## `test_deep_merge_function_still_supports_dicts`

Deep merge must still support:

```python
deep_merge(dict1, dict2)
```

Meaning:

- SprigConfig’s merge engine remains usable as a standalone helper
- Existing consumers are not broken by internal changes

---

# ✔️ Summary

The deep-merge suite exercises representative cases:

| Feature | Behavior exercised |
|--------|-------------------|
| Recursive merge | ✔️ |
| Strict precedence rules | ✔️ |
| Import order matters | ✔️ |
| Nested imports preserved exactly | ✔️ |
| Lists overwrite | ✔️ |
| Circular import detection | ✔️ |
| Dotted-key access after merge | ✔️ |
| Warning suppression flag survives loading | ✔️ |
| Raw dict merge backward compatibility | ✔️ |

The tests cover the particular checked values, fixture profiles, and import
chains listed above; they do not prove all merge orderings or structures behave
identically.

---

## Run

From `sprig-config-module/`:

```bash
poetry run pytest tests/test_deep_merge.py
```
