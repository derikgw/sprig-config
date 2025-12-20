# test_path_traversal.py — Security Tests for Import Path Validation

## Purpose

This test module verifies that `ConfigLoader` properly protects against **path traversal attacks** in configuration imports.

Path traversal vulnerabilities occur when an attacker can use relative paths (e.g., `../../etc/passwd`) to access files outside the intended directory. This is a critical security concern for configuration systems that load files based on user-provided paths.

---

## What This Tests

### 1. **Path Traversal is Blocked** (`test_path_traversal_blocked`)

Verifies that malicious import paths are rejected:

```yaml
imports:
  - ../../etc/passwd  # ❌ Blocked!
```

**Expected Behavior**:
- `ConfigLoader` raises `ConfigLoadError` with message "Path traversal detected"
- The error message includes the offending import path and config directory
- No file is accessed outside the config directory

**Attack Scenarios Prevented**:
- Reading system files (`/etc/passwd`, `/etc/shadow`)
- Accessing parent directories (`../../../`)
- Reading sensitive application files outside config directory
- Directory traversal via symbolic links (resolved paths are validated)

### 2. **Normal Subdirectory Imports Allowed** (`test_normal_subdirectory_imports_allowed`)

Ensures that legitimate subdirectory imports still work:

```yaml
imports:
  - imports/common  # ✅ Allowed - within config_dir/imports/
```

**Expected Behavior**:
- Imports within `config_dir` and its subdirectories work normally
- Files are loaded and merged correctly
- Configuration behaves as expected

---

## Security Implementation

### Validation Logic

The `_resolve_import()` method:

1. Constructs the full path: `config_dir / import_key`
2. Resolves symlinks and relative paths: `.resolve()`
3. Validates the resolved path is within `config_dir`:
   ```python
   try:
       resolved_path.relative_to(config_dir_resolved)
   except ValueError:
       raise ConfigLoadError("Path traversal detected...")
   ```

### Why This Matters

Configuration files may come from:
- User input (uploaded configs, web forms)
- External systems (CI/CD, orchestrators)
- Untrusted sources (third-party integrations)

Without path traversal protection, a malicious configuration could:
- Read sensitive files (credentials, keys, tokens)
- Access system configuration
- Exfiltrate data from the filesystem

---

## Coverage

This test ensures:
- ✅ Upward directory traversal (`../`, `../../`) is blocked
- ✅ Absolute paths outside config_dir are blocked
- ✅ Symbolic link resolution doesn't bypass validation
- ✅ Legitimate subdirectory imports continue to work
- ✅ Error messages are clear and actionable

---

## Defense in Depth

This protection is one layer of a comprehensive security strategy:

1. **Input Validation**: Path traversal protection (this test)
2. **Least Privilege**: Run applications with minimal filesystem permissions
3. **Secret Management**: Use `LazySecret` for sensitive values (prevents logging)
4. **Immutable Config**: `Config` object discourages runtime modification

---

## Related Security Features

- `lazy_secret.py` - Encrypted secrets with deferred decryption
- `config.py` - Immutable-ish config object prevents tampering
- Production profile guards - Missing prod config raises errors

Together, these features provide robust security for production configuration management.
