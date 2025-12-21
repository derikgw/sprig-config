---
layout: default
title: Security
---

# Security

SprigConfig provides secure handling of sensitive configuration values through encrypted secrets with lazy decryption. This guide covers key management, encryption workflow, and security best practices.

---

## Overview

SprigConfig uses **Fernet symmetric encryption** from the `cryptography` library. Sensitive values are stored as `ENC(...)` in configuration files and decrypted only when explicitly accessed.

Key security principles:
- **Encrypt at rest** — Secrets are encrypted in configuration files
- **Decrypt on demand** — Values stay encrypted until `.get()` is called
- **Redact by default** — Dumps and serialization hide secrets
- **Key separation** — Each environment has its own encryption key

---

## Encryption Format

Encrypted values use the `ENC()` wrapper:

```yaml
database:
  username: admin
  password: ENC(gAAAAABl_example_ciphertext_here...)

api:
  key: ENC(gAAAAABl_another_encrypted_value...)
```

SprigConfig automatically detects `ENC()` values and wraps them as `LazySecret` objects.

---

## Key Management

### Generating a key

Use the `cryptography` library to generate a Fernet key:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

Output looks like:
```
ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=
```

### One key per environment

Generate separate keys for each environment:

| Environment | Key Variable |
|-------------|--------------|
| Development | `DEV_SECRET_KEY` or shared `.env` |
| Test | `TEST_SECRET_KEY` or in-memory |
| Production | `APP_SECRET_KEY` via secret manager |

### Storing keys securely

**Never commit keys to version control.**

Store keys in:
- **Secret managers** — HashiCorp Vault, AWS Secrets Manager, Azure Key Vault
- **CI/CD protected variables** — GitLab CI/CD, GitHub Actions secrets
- **Local `.env` files** — Excluded from Git via `.gitignore`
- **Environment variables** — Set at deployment time

### Setting the key

SprigConfig provides multiple ways to configure the encryption key:

#### Option A: Environment variable

```bash
export APP_SECRET_KEY="your-fernet-key-here"
```

SprigConfig checks `APP_SECRET_KEY` automatically when decrypting.

#### Option B: Load from environment explicitly

```python
from sprigconfig.lazy_secret import ensure_key_from_env

# Loads APP_SECRET_KEY and validates it
ensure_key_from_env("APP_SECRET_KEY")
```

#### Option C: Set key directly

```python
from sprigconfig.lazy_secret import set_global_key

set_global_key("your-fernet-key-here")
```

#### Option D: Custom key provider

For key rotation or vault integration:

```python
from sprigconfig.lazy_secret import set_key_provider

def get_key_from_vault():
    # Fetch from secret manager
    return vault_client.get_secret("app-secret-key")

set_key_provider(get_key_from_vault)
```

### Key resolution order

When decrypting, SprigConfig checks for keys in this order:

1. Explicit key passed to `LazySecret`
2. Global key set via `set_global_key()`
3. Dynamic provider via `set_key_provider()`
4. Environment variable `APP_SECRET_KEY`

---

## Encrypting Values

Create a helper script for encrypting values:

```python
# encrypt_value.py
import os
import sys
from cryptography.fernet import Fernet

key = os.environ.get("APP_SECRET_KEY")
if not key:
    print("Set APP_SECRET_KEY first")
    sys.exit(1)

value = sys.argv[1]
f = Fernet(key.encode())
encrypted = f.encrypt(value.encode()).decode()
print(f"ENC({encrypted})")
```

Usage:

```bash
export APP_SECRET_KEY="your-key"
python encrypt_value.py "my-secret-password"
# Output: ENC(gAAAAABl...)
```

Then add to your configuration:

```yaml
database:
  password: ENC(gAAAAABl...)
```

---

## LazySecret Behavior

### Accessing secrets

Encrypted values become `LazySecret` objects:

```python
cfg = load_config(profile="prod")

# Returns LazySecret, not the plaintext
secret = cfg["database"]["password"]
print(type(secret))  # <class 'sprigconfig.lazy_secret.LazySecret'>

# Decrypt only when needed
plaintext = secret.get()
```

### Lazy decryption

Decryption happens only when `.get()` is called:
- Memory contains encrypted ciphertext until access
- Failed decryption raises `ConfigLoadError`
- Each `.get()` call decrypts (no caching of plaintext)

### Memory cleanup

For sensitive applications, use `.zeroize()` for best-effort memory cleanup:

```python
secret = cfg["database"]["password"]
password = secret.get()
# Use password...
secret.zeroize()  # Best-effort cleanup
```

Note: Python's garbage collection makes guaranteed memory cleanup impossible.

---

## Serialization and Redaction

### Default behavior: redacted

Secrets are redacted in dumps and serialization:

```python
cfg = load_config(profile="prod")

# Redacted output
print(cfg.to_dict())
# {'database': {'password': '<LazySecret>'}}

print(cfg.dump())
# database:
#   password: <LazySecret>
```

### Revealing secrets (unsafe)

For debugging, you can reveal secrets:

```python
# In code (unsafe!)
data = cfg.to_dict(reveal_secrets=True)
yaml_str = cfg.dump(safe=False)

# Via CLI (unsafe!)
sprigconfig dump --config-dir=config --profile=prod --secrets
```

**Warning:** Only use reveal options in secure, local environments. Never in logs or CI output.

---

## Key Rotation

### Rotation procedure

1. **Generate new key (K2):**
   ```python
   from cryptography.fernet import Fernet
   new_key = Fernet.generate_key().decode()
   ```

2. **Re-encrypt all secrets with K2:**
   ```python
   old_f = Fernet(old_key)
   new_f = Fernet(new_key)

   # For each secret
   plaintext = old_f.decrypt(old_ciphertext)
   new_ciphertext = new_f.encrypt(plaintext)
   ```

3. **Deploy updated configs + K2 together**

4. **Remove old key (K1) from all environments**

### Dual-key transition (optional)

Use a custom key provider for gradual rotation:

```python
def dual_key_provider():
    k1 = os.getenv("APP_SECRET_KEY_OLD")
    k2 = os.getenv("APP_SECRET_KEY")

    # Try new key first, fall back to old
    return k2 or k1

set_key_provider(dual_key_provider)
```

---

## CI/CD Security

### Pipeline best practices

```yaml
# GitLab CI example
deploy:
  script:
    - pip install sprig-config
    # Key is injected as protected variable
    - sprigconfig dump --config-dir=config --profile=prod  # Redacted
  variables:
    APP_SECRET_KEY: $PROD_SECRET_KEY  # Protected CI variable
```

### Security checklist

- [ ] `APP_SECRET_KEY` is a protected/masked CI variable
- [ ] Never echo or log secret keys
- [ ] Never use `--secrets` flag in CI logs
- [ ] Config dumps go to artifacts, not logs
- [ ] Different keys for each environment

---

## Error Handling

### Common errors

| Error | Cause |
|-------|-------|
| `No Fernet key available` | Key not set before accessing secret |
| `Invalid Fernet key` | Key is malformed or wrong length |
| `InvalidToken` | Wrong key or corrupted ciphertext |
| `ConfigLoadError` | Wraps cryptography errors |

### Handling decryption errors

```python
from sprigconfig import load_config, ConfigLoadError

try:
    cfg = load_config(profile="prod")
    password = cfg["database"]["password"].get()
except ConfigLoadError as e:
    if "Fernet key" in str(e):
        print("Missing or invalid encryption key")
    elif "InvalidToken" in str(e):
        print("Wrong key or corrupted secret")
    else:
        print(f"Config error: {e}")
```

---

## Security Audit Checklist

### Configuration files

- [ ] All sensitive values use `ENC()` wrapper
- [ ] No plaintext passwords in any environment
- [ ] No keys or tokens visible in files
- [ ] `.gitignore` excludes `.env` files

### Key management

- [ ] One key per environment
- [ ] Keys stored in secret manager or protected variables
- [ ] Keys rotated periodically
- [ ] Old keys removed after rotation

### Code practices

- [ ] Secrets accessed only when needed
- [ ] No logging of decrypted values
- [ ] `reveal_secrets` only used locally
- [ ] Key provider used for vault integration

### Verification commands

```bash
# Check for unencrypted sensitive values
grep -rn "password:" config/ | grep -v "ENC("
grep -rn "secret:" config/ | grep -v "ENC("
grep -rn "token:" config/ | grep -v "ENC("

# Verify all ENC values are present
grep -rn "ENC(" config/
```

---

## Best Practices Summary

1. **Encrypt everything sensitive** — Passwords, API keys, tokens
2. **Never commit keys** — Use secret managers or CI variables
3. **Use separate keys per environment** — Dev keys don't work in prod
4. **Decrypt only when needed** — Keep secrets lazy
5. **Redact by default** — Only reveal for debugging
6. **Rotate keys periodically** — At least annually
7. **Audit regularly** — Check for plaintext secrets

---

[← Back to Documentation](index.md)
