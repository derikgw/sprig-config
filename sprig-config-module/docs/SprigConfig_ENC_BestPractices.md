# SprigConfig — Secrets & `ENC(...)` Best Practices  
**Updated for the global‑key API, enhanced LazySecret behavior, and secure dump rules**

SprigConfig supports encrypted configuration values using `ENC(...)` wrappers combined with a centrally managed Fernet key. This document explains key generation, encryption workflow, runtime usage, and operational security guidance.

---

## 1. Key Material

SprigConfig uses **Fernet keys** from the `cryptography` package.

### Generate a key

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### Storage & handling
- Create **one Fernet key per environment** (dev, test, stage, prod).
- Never commit keys into source control.
- Store only in:
  - Secret managers (Vault, AWS SM, GitLab Protected CI variables, etc.)
  - Local `.env` files **excluded from Git**
  - Encrypted credential stores
- Keys are **never** stored in YAML.

---

## 2. SprigConfig Global-Key API (New)

You must configure the Fernet key **before** loading encrypted configs.

### Option A — Load directly from environment

```python
from sprigconfig.lazy_secret import ensure_key_from_env
ensure_key_from_env("APP_SECRET_KEY")
```

### Option B — Set the key directly

```python
from sprigconfig.lazy_secret import set_global_key
set_global_key("<base64-fernet-key>")
```

### Option C — Provide a custom key provider

Useful for rotations or retrieving keys from a vault:

```python
from sprigconfig.lazy_secret import set_key_provider

def retrieve_key():
    return os.getenv("APP_SECRET_KEY")

set_key_provider(retrieve_key)
```

The key is validated immediately and raises `ConfigLoadError` if invalid.

---

## 3. Encrypting Values

Create a helper script that reads the Fernet key and outputs encrypted strings:

```bash
export APP_SECRET_KEY="<key>"
python encrypt_value.py "superSecret"
```

Write encrypted values in YAML as:

```yaml
db:
  password: ENC(gAAAAABcExampleCiphertextHere)
```

SprigConfig automatically detects and wraps these as `LazySecret` objects.

---

## 4. Runtime Behavior of LazySecret (Updated)

Encrypted fields become `LazySecret` instances.

### Access plaintext explicitly

```python
pwd = cfg["db"]["password"].get()
```

Important characteristics:

- Decryption happens **only on demand**.
- Values remain encrypted in memory until `.get()` is called.
- Never log decrypted values.
- Avoid storing decrypted values in long-lived structures.

### Serialization rules

- `Config.to_dict()` **redacts** all secrets by default.
- `Config.to_dict(reveal_secrets=True)` returns plaintext — **unsafe**, use only for debugging.
- YAML dumps via `.dump()` follow the same redaction rules.

---

## 5. Processing Order

SprigConfig processes configuration in this sequence:

1. Load `application.yml`
2. Load `application-<profile>.yml`
3. Apply overlays and **deep merge**
4. Resolve recursive imports and detect cycles
5. Apply `${ENV}` expansions
6. Wrap `ENC(...)` values as `LazySecret`

This ensures encryption refers to the final resolved value.

---

## 6. Key Rotation

Recommended approach:

1. Generate new key **K2**.
2. Re-encrypt all secrets with **K2**.
3. Deploy updated configs + K2 simultaneously.
4. Remove old key **K1** from all environments.

### Optional dual‑key mode
Using a custom key provider, you may temporarily support:

- Decrypt with K1 or K2  
- Re-encrypt exclusively with K2  

This permits staggered rollouts.

---

## 7. CI/CD & Local Development

### CI/CD pipelines

- Inject `APP_SECRET_KEY` via secure CI variables.
- Do not echo secrets or decrypted values.
- Disable reveal mode except in manual debugging jobs.
- Avoid printing full config dumps unless redacted.

### Local development

- Use a `.env` file that is **git‑ignored**.
- Use `python‑dotenv` if convenient.
- Regenerate dev keys freely—dev secrets should never be production-realistic.

---

## 8. CLI Dump Behavior (New)

SprigConfig's CLI supports safe debugging.

### Redacted dump (default)

```bash
sprigconfig dump config/
```

### Reveal dump (unsafe—plaintext)

```bash
sprigconfig dump --reveal config/
```

Always avoid `--reveal` in shared logs or CI.

---

## 9. Auditing & Quality Checks

Regularly verify:

- All sensitive fields use `ENC(...)`
- `APP_SECRET_KEY` is present in each environment
- No plaintext passwords appear in commit history  
- Imports and overlays do not accidentally introduce unencrypted secrets

Tools:

```bash
grep -R "ENC(" -n config/
grep -R "password:" -n config/
```

---

## 10. Failure Modes & Errors

- Missing key → `ConfigLoadError("No Fernet key available …")`
- Invalid key → immediate validation error in `set_global_key`
- Corrupted ciphertext → `InvalidToken` wrapped as `ConfigLoadError`
- Attempting to decrypt without configured key → `ConfigLoadError`

---

## 11. Summary

SprigConfig’s secret-handling philosophy:

- **Encrypt everything sensitive at rest**
- **Never commit keys**
- **Load keys only from trusted sources**
- **Decrypt only when explicitly needed**
- **Redact by default**
- **Support clean rotation**

This ensures your configuration system remains secure, predictable, and maintainable across all environments.

---

If you need an additional version of this document (PDF, DOCX, GitLab‑formatted README, or an example encryption helper), I can generate it anytime.
