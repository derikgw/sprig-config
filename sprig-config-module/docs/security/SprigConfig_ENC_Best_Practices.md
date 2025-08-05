# 🔐 Secrets Management with SprigConfig ENC()

SprigConfig supports secure storage of sensitive values in configuration files using the `ENC()` format. This allows you to keep secrets encrypted at rest while still loading them into your application at runtime.

---

## 📦 How ENC() Works
SprigConfig uses [Fernet encryption](https://cryptography.io/en/latest/fernet/) (AES-128 + HMAC-SHA256) to:
- Encrypt sensitive values (outside of runtime) into `ENC(...)` format
- Decrypt values transparently at runtime using a master key

**Example:**
```yaml
secrets:
  username: ENC(gAAAAABokVDE6uM8TItupVCEB9URRjbKzxO5bddjHPPBG_9NGjinUdhq3P0sLYFQ76gRrt87Yy3haINdh2_NrO7KobeKokz37A==)
  password: ENC(gAAAAABokVDE3fwikJO6YqTStG4xnh5cPjWNAT3JXw0zB-HDtdqCCRGvNBNogl2yVQDedyvfffc44e2guTs8JHZpD7sBaOqEmQ==)
```

At runtime:
- SprigConfig detects `ENC(...)` values
- Decrypts them using `APP_SECRET_KEY`
- Provides plaintext values to your application

---

## 🚦 Workflow Overview
1. **Generate a master key** (Fernet key)
2. **Encrypt values** into `ENC(...)` using developer tooling (`sprig-tools`)
3. **Commit ENC values** to config files (never plaintext)
4. **Deploy application** with `APP_SECRET_KEY` provided securely at runtime
5. **SprigConfig decrypts automatically** when loading configuration

---

## 🔑 Generating a Master Key
Use `sprig-tools` (developer-only CLI):
```bash
sprig-secrets generate-key
```
Output:
```
Generated key: KX5QdVVuBbpqQU9ujKdzBqFtZxvXk80QXUjcD1T21sw=
⚠️ Store this securely (Vault, AWS Secrets Manager, Azure Key Vault)
```

---

## 🔒 Encrypting Values
Encrypt secrets using the same CLI:
```bash
export APP_SECRET_KEY=<your-key>
sprig-secrets encrypt "superSecretPass"
```
Output:
```
ENC(gAAAAABokVDE...)
```
Paste the `ENC(...)` value into your config file.

---

## 🔓 Decrypting Values (Developer Convenience)
For debugging only:
```bash
export APP_SECRET_KEY=<your-key>
sprig-secrets decrypt "ENC(gAAAAABokVDE...)"
```
Output:
```
superSecretPass
```
**⚠️ Never run decrypt in production pipelines or logs.**

---

## ⚠️ Best Practices
### ✅ Do
- Store `APP_SECRET_KEY` in a secrets manager (Vault, AWS Secrets Manager, Azure Key Vault)
- Use `.env` **only for local development** and ensure `.env` is `.gitignore`d
- Keep encryption logic (`encrypt_secret()`) **out of runtime** — only decrypt at runtime
- Rotate keys if compromised (consider versioning: `ENC[v2](...)`)

### 🚫 Don’t
- Commit `APP_SECRET_KEY` to version control
- Use the same key for development, staging, and production
- Log decrypted secrets

---

## 🛡 Key Rotation (Future Recommendation)
For forward compatibility, SprigConfig can support versioned keys:
```
ENC[v1](...)
ENC[v2](...)
```
At runtime, the correct key is chosen based on the version tag. This allows:
- Generating new keys without breaking old secrets
- Incremental re-encryption

---

## 📌 Summary
SprigConfig ENC provides:
- Secure encryption for configuration secrets
- Clear separation between **runtime decryption** and **developer encryption**
- Compatibility with enterprise-grade secret management
- Support for future enhancements like key rotation

By following these best practices, you can keep secrets safe across all environments while maintaining Spring Boot–style convenience.
