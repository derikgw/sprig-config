# Secrets API

SprigConfig provides secure secret management through the `LazySecret` class, which handles encrypted configuration values.

## LazySecret

A secure wrapper for encrypted configuration values that provides lazy decryption and automatic redaction.

::: sprigconfig.lazy_secret.LazySecret
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - get
        - encrypt
        - set_global_key_provider
        - __repr__
        - __str__

---

## Usage Patterns

### Basic Secret Usage

```python
from sprigconfig import load_config

cfg = load_config()

# Secret is still encrypted at this point
db_password = cfg["database"]["password"]  # LazySecret object

# Decrypt only when needed
actual_password = db_password.get()  # "my-secret-password"
```

### Encrypting Secrets

```python
from sprigconfig.lazy_secret import LazySecret
import os

# Get encryption key from environment
key = os.environ["APP_SECRET_KEY"]

# Encrypt a secret
encrypted = LazySecret.encrypt("my-secret-value", key)
print(encrypted)  # ENC(gAAAAAB...)

# Use in configuration file
# database:
#   password: ENC(gAAAAAB...)
```

### Global Key Provider

For advanced scenarios, set a global key provider instead of using environment variables:

```python
from sprigconfig.lazy_secret import LazySecret

def get_key_from_vault():
    # Fetch key from HashiCorp Vault, AWS Secrets Manager, etc.
    return fetch_from_vault("encryption-key")

# Set global key provider
LazySecret.set_global_key_provider(get_key_from_vault)

# Now all LazySecret.get() calls will use this key
cfg = load_config()
password = cfg["database"]["password"].get()  # Uses global provider
```

### Per-Secret Keys

For maximum security, use different keys for different secrets:

```python
from sprigconfig.lazy_secret import LazySecret

# Encrypt with specific key
db_key = "db-specific-encryption-key"
encrypted_db_pass = LazySecret.encrypt("db-password", db_key)

# Later, decrypt with the same key
db_password = cfg["database"]["password"]
actual_password = db_password.get(key=db_key)
```

---

## ENC() Format

Secrets in configuration files use the `ENC()` format:

```yaml
# config/application.yml
database:
  host: localhost
  username: admin
  password: ENC(gAAAAABm...)  # Encrypted with Fernet

api:
  key: ENC(gAAAAABn...)  # Another encrypted value
```

When SprigConfig loads this file:
1. Detects `ENC(...)` values
2. Creates `LazySecret` objects (not yet decrypted)
3. Decryption happens only when `.get()` is called

---

## Security Features

### Lazy Evaluation

Secrets are not decrypted until explicitly requested:

```python
# Load config - secrets remain encrypted
cfg = load_config()

# Access secret object - still encrypted
secret = cfg["api"]["key"]  # LazySecret object

# Decrypt only when needed
api_key = secret.get()  # Now decrypted
```

**Benefits:**
- Prevents accidental exposure in logs
- Reduces attack surface
- Secrets stay encrypted in memory until needed

### Automatic Redaction

LazySecret objects are automatically redacted in string representations:

```python
secret = cfg["database"]["password"]

print(secret)           # LazySecret(redacted)
print(repr(secret))     # LazySecret(redacted)
print(str(secret))      # LazySecret(redacted)

# Only .get() reveals the actual value
print(secret.get())     # my-secret-password
```

This prevents accidental exposure in:
- Log files
- Error messages
- Debug output
- Exception tracebacks

### Key Management

SprigConfig supports multiple key sources (in priority order):

1. **Explicit key parameter**: `secret.get(key="specific-key")`
2. **Global key provider**: `LazySecret.set_global_key_provider(provider_func)`
3. **Environment variable**: `APP_SECRET_KEY`

```python
import os
from sprigconfig.lazy_secret import LazySecret

# Method 1: Environment variable (simplest)
os.environ["APP_SECRET_KEY"] = "your-fernet-key"

# Method 2: Global provider (flexible)
def get_key():
    return fetch_from_secret_manager()

LazySecret.set_global_key_provider(get_key)

# Method 3: Explicit key (per-secret)
password = secret.get(key="specific-key-for-this-secret")
```

---

## Encryption Details

SprigConfig uses **Fernet** (symmetric encryption) from the `cryptography` library:

- **Algorithm**: AES-128-CBC with HMAC-SHA256
- **Key size**: 32 bytes (URL-safe base64-encoded)
- **Security**: Authenticated encryption (prevents tampering)

### Generating Keys

```python
from cryptography.fernet import Fernet

# Generate a new key
key = Fernet.generate_key()
print(key.decode())  # Use this as APP_SECRET_KEY
```

Or via command line:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Best Practices

### 1. Never Commit Keys

❌ **Don't do this:**
```yaml
# .env (committed to git)
APP_SECRET_KEY=my-secret-key-here
```

✅ **Do this instead:**
```bash
# Set in environment (not committed)
export APP_SECRET_KEY="key-from-vault"
```

### 2. Use Different Keys Per Environment

```bash
# Development
export APP_SECRET_KEY="dev-key-12345..."

# Production (from secret manager)
export APP_SECRET_KEY="$(aws secretsmanager get-secret-value ...)"
```

### 3. Minimize Secret Access

```python
# ❌ Bad: Decrypt early and store
db_password = cfg["database"]["password"].get()
app.config["DB_PASSWORD"] = db_password  # Now in memory as plaintext

# ✅ Good: Decrypt only when needed
def connect_to_db():
    password = cfg["database"]["password"].get()  # Decrypt on use
    return create_connection(password=password)
```

### 4. Rotate Keys Periodically

When rotating encryption keys:

1. Generate new key
2. Decrypt secrets with old key
3. Re-encrypt with new key
4. Update configuration files
5. Deploy new key to environments

### 5. Prefer Environment Variables in Production

For production systems, consider using environment variables directly instead of encrypted config files:

```yaml
# config/application-prod.yml
database:
  password: ${DB_PASSWORD}  # From environment

api:
  key: ${API_KEY}  # From environment
```

---

## Error Handling

```python
from sprigconfig import load_config
from sprigconfig.lazy_secret import LazySecret

cfg = load_config()

try:
    password = cfg["database"]["password"].get()
except Exception as e:
    # Handle decryption errors
    print(f"Failed to decrypt secret: {e}")
```

Common errors:
- **Invalid key**: Key doesn't match the one used for encryption
- **Missing key**: No key provider configured
- **Corrupted ciphertext**: ENC() value is malformed

---

## Examples

See the [Secrets Example](https://gitlab.com/dgw_software/sprig-config/-/tree/main/sprig-config-module/examples/secrets) for complete working code demonstrating:

- Key generation
- Secret encryption
- Configuration file setup
- Decryption patterns
- Best practices

---

## Related Documentation

- [Security Guide](../security.md) - Overall security best practices
- [Best Practices Guide](../../sprig-config-module/docs/SprigConfig_ENC_BestPractices.md) - Detailed encryption patterns
- [Configuration Guide](../configuration.md) - General configuration usage
