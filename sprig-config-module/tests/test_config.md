# Documentation for `tests/test_config.py`

This document explains the purpose and behavior exercised
by the tests in:

```
tests/test_config.py
```

These tests exercise the current
`Config` class — the object returned by both `ConfigLoader` and
`load_config()`.  
They provide regression evidence for the specific behaviors asserted below.

---

# 🎯 Purpose of This Test Suite

The suite checks that `Config`:

- Behaves as a mapping
- Wraps nested dictionaries in selected access paths
- Capable of **dotted-key lookup**
- Able to serialize cleanly via `to_dict()` and `dump()`
- Supports tested dict-style access (`cfg["key"]`, iteration, etc.)

The tests do not establish that `Config` is immutable: they check selected
lookup, copy, and serialization behavior only.

---

# 🧱 1. Basic Construction Tests

## `test_config_wraps_dicts_recursively`

Ensures:

- Constructing `Config(data)` wraps all nested dicts automatically.
- `cfg["a"]["b"]["c"]` behaves naturally.
- Shallow values remain unchanged.

**Why:**  
Users should be able to descend into config structures without switching types.

---

## `test_config_is_mapping_like`

Validates the Mapping API:

- `keys()`
- `items()`
- Iteration
- Membership testing (`"a" in cfg`)

**Why:**  
These assertions check compatibility with the mapping operations used by callers.

---

# 🔍 2. Dotted-Key Access

## `test_dotted_key_access`

Ensures:

- `cfg.get("etl.jobs.root")` resolves deeply nested values.
- Partial dotted access (e.g., `"etl.jobs"`) returns either:
  - the raw underlying dict  
  - *or* a `Config` wrapper  

**Why:**  
Dotted-key lookup is one of SprigConfig’s major user-facing conveniences.

---

## `test_dotted_key_missing_returns_default`

Ensures:

- Missing dotted paths return `default` when provided.
- When no default is given, return `None`.

**Why:**  
Makes dotted-key access safe and ergonomic.

---

## `test_dotted_key_nesting_does_not_modify_data`

Verifies:

- Lookup must NOT mutate underlying data structures.

**Evidence scope:**
This checks that the tested lookup does not mutate the source data. It does not
establish that `Config` is immutable.

---

# 🧭 3. Nested Access (Dict-Like)

## `test_nested_access_returns_config`

Ensures `cfg["a"]` returns a `Config` when the value is a nested dict.

---

## `test_nested_missing_key_raises_keyerror`

Ensures:

- `cfg["missing"]` raises `KeyError`, mirroring dict semantics.

---

# 📤 4. `to_dict()` Behavior

## `test_to_dict_returns_plain_dict`

Ensures:

- Returns a **deep copy**, not the original dict.
- Fully expands nested `Config` wrappers into raw dicts.

---

## `test_to_dict_recursively_converts_nested_config`

Ensures:

- Any nested `Config` instances are recursively converted back to dicts.

**Why:**  
Serialization functions depend on this.

---

# 📄 5. `dump()` Behavior

## `test_config_dump_writes_yaml`

Verifies:

- `cfg.dump(path)` writes a valid YAML file.
- Output YAML matches the underlying data.

---

# 🧪 Summary

These tests exercise selected public behaviors of `Config`.

| Feature | Behavior exercised |
|--------|-------------------|
| Mapping-like behavior | ✔️ |
| Recursive wrapping | ✔️ |
| Dotted-key access | ✔️ |
| Default handling | ✔️ |
| No mutation during access | ✔️ |
| `to_dict()` deep-copy semantics | ✔️ |
| YAML dumping | ✔️ |

Secret redaction, explicit reveal, and reveal-failure checks are centralized in
[`security_tests/`](../security_tests/README.md).

## Run

From `sprig-config-module/`:

```bash
poetry run pytest tests/test_config.py
```
