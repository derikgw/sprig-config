# Secrets Management Example

This example demonstrates how to securely handle sensitive configuration data using SprigConfig's encrypted secrets feature.

## Files

- `config/application.yml` - Configuration with encrypted secrets
- `config/application-secrets.yml` - Example of profile-specific secrets
- `example.py` - Python script demonstrating secret handling
- `.env.example` - Template for environment variables

## What You'll Learn

- Encrypting secrets with ENC() format
- Lazy secret evaluation (decrypt only when accessed)
- Secret redaction in config dumps
- Managing encryption keys
- Best practices for secret handling

## Setup

1. Generate an encryption key:

```bash
# Using Python
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

2. Set the encryption key as an environment variable:

```bash
export APP_SECRET_KEY="your-generated-key-here"
```

3. Encrypt a secret value:

```python
from sprigconfig.lazy_secret import LazySecret

# Encrypt a value
encrypted = LazySecret.encrypt("my-secret-password", "your-generated-key-here")
print(encrypted)  # ENC(gAAAAA...)
```

## Running the Example

```bash
# Set your encryption key
export APP_SECRET_KEY="your-key-here"

# Run the example
python example.py
```

## Expected Output

```
Configuration with Secrets:
  Database password: [LazySecret - not yet decrypted]
  API key: [LazySecret - not yet decrypted]

Decrypted values (use with caution):
  Database password: my-secret-db-password
  API key: sk-1234567890abcdef

Config dump (secrets are redacted):
{
  "database": {
    "password": "**REDACTED**"
  },
  "api": {
    "key": "**REDACTED**"
  }
}
```

## Key Concepts

### ENC() Format

Secrets are stored in configuration files using the `ENC()` format:

```yaml
database:
  password: ENC(gAAAAABm...)  # Encrypted ciphertext
```

### LazySecret Objects

When SprigConfig loads a config file with `ENC()` values, it creates `LazySecret` objects:

- **Not decrypted automatically** - prevents accidental exposure
- **Decrypt on demand** - call `.get()` to decrypt
- **Automatic redaction** - not shown in logs or config dumps

### Example Usage

```python
from sprigconfig import load_config

cfg = load_config()

# The secret is still encrypted at this point
db_password = cfg["database"]["password"]  # LazySecret object

# Decrypt only when needed
actual_password = db_password.get()  # "my-secret-password"
```

### Security Best Practices

1. **Never commit encryption keys** - use environment variables
2. **Use different keys per environment** - dev, test, prod
3. **Rotate keys periodically** - re-encrypt secrets with new keys
4. **Minimize secret access** - decrypt only when absolutely needed
5. **Use environment variables for production** - instead of encrypted files
6. **Audit secret access** - log when secrets are decrypted

### Key Management

SprigConfig supports multiple key sources:

1. **Environment variable** (recommended):
   ```bash
   export APP_SECRET_KEY="your-key-here"
   ```

2. **Global key provider**:
   ```python
   from sprigconfig.lazy_secret import LazySecret

   LazySecret.set_global_key_provider(lambda: get_key_from_vault())
   ```

3. **Per-secret key** (advanced):
   ```python
   secret.get(key="specific-key-for-this-secret")
   ```

## Common Use Cases

### Development
- Encrypt non-sensitive mock values
- Share encrypted configs in version control
- Each developer has their own encryption key

### Testing
- Use test-specific keys
- Encrypt test credentials for CI/CD
- Verify secret handling behavior

### Production
- Use environment variables for secrets (preferred)
- Or use encrypted configs with keys from secret management service
- Implement key rotation strategy

## Next Steps

- Read the [Security Documentation](https://dgw-software.gitlab.io/sprig-config/security/)
- Check `docs/SprigConfig_ENC_BestPractices.md` for advanced patterns
- Try the **web-app** example to see secrets in a real application
