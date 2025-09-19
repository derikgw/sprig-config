# SprigConfig — Secrets & `ENC(...)` Best Practices

This note collects pragmatic guidance for managing encrypted secrets in SprigConfig.

## 1) Key material
- Use a **Fernet key** for `APP_SECRET_KEY` (`cryptography` library).
- Generate once per environment:
  ```python
  from cryptography.fernet import Fernet
  print(Fernet.generate_key().decode())
  ```
- Store **only** in secure env storage (vault/secret manager, CI/CD secrets, local `.env` excluded from VCS). Never commit keys.

## 2) Encrypting values
- Use a local helper (example):
  ```bash
  export APP_SECRET_KEY='<fernet-key>'
  python encrypt_value.py 'superSecret'  # outputs ciphertext
  ```
- Save ciphertext to YAML as `ENC(<ciphertext>)`:
  ```yaml
  db:
    password: ENC(gAAAAABn...)
  ```

## 3) Decryption at runtime
- The loader wraps values as `LazySecret`.
- Access plaintext only via `.get()`:
  ```python
  pwd = cfg["db"]["password"].get()
  ```
- Avoid logging decrypted values. Keep them in memory as briefly as possible.

## 4) Rotation
- Create a **new** key (K2), re‑encrypt secrets, roll out, then revoke the old key (K1).
- During rotation windows, you may temporarily support **dual** decryption via app code if needed; otherwise cutover all configs at once.

## 5) CI/CD & local dev
- In CI, inject `APP_SECRET_KEY` from your secrets store.
- For local dev, use `.env` that is **git‑ignored** and load with `python-dotenv` if desired.
- Never print secrets in pipeline logs. Prefer redaction when dumping configs.

## 6) Auditing
- Grep for `ENC(` to ensure everything sensitive is encrypted.
- Periodically verify that `APP_SECRET_KEY` is present in each environment.

## 7) Pitfalls
- Missing key → `ConfigLoadError` if an `ENC(...)` must be decrypted.
- Editing YAML on Windows with BOM: prefer UTF‑8 without BOM. The loader is BOM‑safe (`utf-8-sig`) but it's best to avoid BOM in source control.
