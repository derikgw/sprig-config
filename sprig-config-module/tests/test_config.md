# Documentation for `tests/test_config.py`

This document explains the purpose, design goals, and expected behavior defined
by the tests in:

```
tests/test_config.py
```

These tests collectively define the **specification** for the future
`Config` class — the object returned by both `ConfigLoader` and
`load_config()`.  
They represent a **contract**, ensuring stability, clarity, and correctness in
SprigConfig’s configuration representation.

The Markdown file corresponds directly to:

```
tests/test_config.md
```

---

# 🎯 Purpose of This Test Suite

`Config` is intended to be:

- A **read-only Mapping**
- A wrapper around nested dicts  
- Capable of **dotted-key lookup**
- Able to serialize cleanly via `to_dict()` and `dump()`
- Safe by default in how it handles `LazySecret`
- Fully backward compatible with dict-style access (`cfg["key"]`, iteration, etc.)

This test suite is a **blueprint for the implementation**.  
If a behavior is expressed here, the final `Config` class MUST adhere to it.

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
The `Config` object must behave like a Python mapping to support existing code.

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

**Why:**  
Protects consumers who rely on immutability and deep copies.

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

# 🔒 6. Secret Redaction & Exposure Rules

## `test_config_to_dict_redacts_lazysecret`

Ensures:

- When converting to a plain dict,
- `LazySecret` is replaced by the placeholder:

```
<LazySecret>
```

**Why:**  
Never expose secrets by default.

---

## `test_config_dump_redacts_lazysecret`

Ensures:

- YAML dump redacts secrets (`safe=True`).

---

## `test_config_dump_can_output_plaintext_secrets`

Uses monkeypatching to override `LazySecret.get()`.

Ensures:

- `dump(..., safe=False)` outputs decrypted secrets.

**Why:**  
Accessible only when explicitly requested.

---

## `test_config_dump_raises_if_cannot_reveal_secret`

Ensures:

- Attempting `safe=False` when no key is available raises `ConfigLoadError`.

**Why:**  
Fail fast rather than silently omitting secrets.

---

# 🧪 Summary

These tests define the **intended public interface** of the `Config` object.

| Feature | Required Behavior |
|--------|-------------------|
| Mapping-like behavior | ✔️ |
| Recursive wrapping | ✔️ |
| Dotted-key access | ✔️ |
| Default handling | ✔️ |
| No mutation during access | ✔️ |
| `to_dict()` deep-copy semantics | ✔️ |
| YAML dumping | ✔️ |
| Secret redaction | ✔️ |
| Secret exposure rules | ✔️ |

The suite ensures the `Config` class is intuitive, safe, consistent, and powerful.

---

If you'd like, I can also generate a **developer README** describing how to implement `Config` to satisfy this test suite.

