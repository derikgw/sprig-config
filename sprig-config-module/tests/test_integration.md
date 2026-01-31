# SprigConfig Full-System Integration Test Documentation

This document describes the purpose and behavior of the integration tests defined in:

```
tests/test_integration.py
```

These tests validate the complete configuration-loading pipeline of **SprigConfig RC3**, ensuring correct merging, metadata injection, secret handling, environment expansion, and backward compatibility.

---

## 🧪 Purpose of These Tests

The integration suite verifies:

- Correct merging of base + profile + imports + nested imports  
- Backward compatibility of `load_config()`  
- Accurate metadata injection under `sprigconfig._meta`  
- Proper handling and decryption of `LazySecret`  
- Environment variable expansion  
- Singleton behavior and isolation  
- Dotted-key access functionality  
- Circular import detection  
- Ability to use `APP_CONFIG_DIR` when no directory is explicitly provided  

These tests represent **end-to-end validation** of the SprigConfig system.

---

# 📝 Test-by-Test Explanation

## 1. Legacy API Support

### `test_load_config_legacy_api_still_works`
Ensures:
- `load_config()` behaves consistently with earlier versions.
- The returned object is a `Config` instance.
- Metadata such as `sprigconfig._meta.profile` is injected properly.

**Why:**  
Backward compatibility is key for dependent systems (e.g., ETL Service Web).

---

## 2. Full Merge Behavior

### `test_full_merge_dev_profile`
Validates:
- Base + profile overlays work.
- Imports and nested imports are resolved.
- Final merged values match expectations.
- Runtime profile metadata is intact.

### `test_full_merge_nested_profile`
Ensures nested import chains (imports inside imports) merge properly.

### `test_full_merge_chain_profile`
Verifies multi-step import chains (`A → B → C`) merge in order.

**Why:**  
Configuration merging is the core feature of SprigConfig—these tests prevent regressions.

---

## 3. Circular Import Detection

### `test_integration_circular_import`
Ensures circular imports raise `ConfigLoadError` with:
- A clear "Circular import detected" message
- The full cycle path displayed (e.g., `a.yml -> b.yml -> a.yml`)
- Arrow notation showing the import chain

**Why:**
Prevents infinite recursion during config resolution and provides actionable error messages for debugging.

---

## 4. Dotted-Key Access

### `test_integration_dotted_key_access`
Checks:
- Deep nested values resolve via dotted keys.
- Metadata still present.

**Why:**  
Dotted-key access is a user-facing convenience feature.

---

## 5. Environment Variable Expansion

### `test_integration_env_var_expansion`
Tests:
- `${ENV_VAR}` substitution.
- `${ENV_VAR:default}` fallback behavior.

**Why:**  
Environment-based config is essential for container deployments.

---

## 6. Secret Handling

### `test_integration_secrets_wrapped`
Validates that encrypted `ENC(...)` values are wrapped in `LazySecret`.

### `test_integration_secret_decryption`
Confirms decryption works using `APP_SECRET_KEY`.

**Why:**  
Security-sensitive functionality must never regress.

---

## 7. APP_CONFIG_DIR Default Behavior

### `test_app_config_dir_env_var`
Ensures:
- When `config_dir=None`, SprigConfig loads from `APP_CONFIG_DIR`.

**Why:**  
Required for production deployments and CLI usage.

---

## 8. Singleton Behavior

### `test_integration_singleton_independent_of_loader`
Ensures `ConfigSingleton` does not reuse `load_config()` results.

### `test_integration_singleton_dotted_keys`
Verifies:
- Singleton initialization works.
- Dotted-key access functions correctly in the singleton.

**Why:**  
The singleton is widely used in long-running services.

---

# ✔️ Summary

This test suite is **legitimate**, **high-value**, and **crucial** for guaranteeing the correctness of:

- Core merge logic  
- Environment expansion  
- Secret handling  
- Metadata injection  
- API backward compatibility  
- Import resolution  
- Singleton behavior  

Every test validates a meaningful and intentional part of SprigConfig’s design.

