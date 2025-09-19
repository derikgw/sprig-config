# 🌱 SprigConfig

SprigConfig is a tiny, opinionated configuration loader for Python apps. It merges layered YAML files, expands `${ENV_VARS}`, supports `imports`, lazy‑decrypts secrets written as `ENC(...)`, and **injects the active profile from the runtime** (env/param), not from files.

**Key features**
- Profile **injection**: `app.profile` is injected from `APP_PROFILE` (or `load_config(profile=...)`). Any `app.profile` in files is ignored, with a warning.
- Deep merge with helpful “partially overridden” warnings.
- `imports` chaining for modular configs.
- `${VAR:default}` environment expansion.
- `ENC(...)` secrets → `LazySecret` (decrypted on access) via `APP_SECRET_KEY`.
- Production guardrails for `logging.level`.
- BOM‑safe YAML reads (`utf-8-sig`) to avoid weird `ï»¿` keys on Windows.

---

## 📦 Install
```bash
pip install sprigconfig
# or
poetry add sprigconfig
```

---

## 📂 Config Layout
```
config/
  application.yml
  application-dev.yml
  application-test.yml
  application-prod.yml
  features.yml
  override.yml
```

### Minimal `application.yml` (no profile here)
```yaml
server:
  port: 8080
logging:
  level: INFO
```

### Example `application-dev.yml`
```yaml
server:
  port: 9090
imports:
  - features.yml
  - override.yml
```

### Example `features.yml`
```yaml
features:
  cache:
    ttl: 300
  auth:
    enabled: true
    methods: ["password"]
```

### Example `override.yml`
```yaml
server:
  port: 9999
features:
  auth:
    methods: ["password", "oauth"]
```

---

## ⚙️ Runtime Selection & Injection

The active profile is determined by:
1) `load_config(profile="...")` argument, else
2) `APP_PROFILE` env var, else
3) if running under `pytest` → `"test"`, otherwise `"dev"`

After merging, the loader injects:
```yaml
app:
  profile: <active>
```

If a file contains `app.profile`, you’ll see a warning like:
```
Ignoring app.profile from files (...); using active profile dev. Consider removing app.profile from files to avoid confusion.
```

---

## 🐍 Use in Python
```python
import os
from sprigconfig import load_config

os.environ["APP_PROFILE"] = "dev"  # or use profile=... in load_config()
cfg = load_config()                # merges base -> profile -> imports
print(cfg["app"]["profile"])       # "dev" (injected)
print(cfg["server"]["port"])       # 9999 (from override.yml)
```

**Config directory**
- Default: `./config` (CWD)
- Override with `APP_CONFIG_DIR=/path/to/config` or `load_config(config_dir=Path(...))`

---

## 🔐 Secrets with `ENC(...)`

You can put encrypted values *anywhere*:
```yaml
secrets:
  username: ENC(gAAAAABn...)
  password: ENC(gAAAAABn...)
```

They are loaded as `LazySecret` objects and decrypted **on first access** using `APP_SECRET_KEY` (a Fernet key).

**Decrypt at runtime**
```python
from sprigconfig.lazy_secret import LazySecret

val = cfg["secrets"]["password"]
assert isinstance(val, LazySecret)
print(val.get())  # plaintext
```

**Encrypting values (quick script)**
```python
# encrypt_value.py
import os, sys
from cryptography.fernet import Fernet

key = os.environ.get("APP_SECRET_KEY")
if not key:
    print("APP_SECRET_KEY missing", file=sys.stderr); sys.exit(1)
if isinstance(key, str):
    key = key.encode()

f = Fernet(key)
ct = f.encrypt(sys.argv[1].encode()).decode()
print(ct)
```
Usage:
```bash
export APP_SECRET_KEY='<your-fernet-key>'
python encrypt_value.py 'superSecret'
# => paste into YAML as ENC(<output>)
```

See **“Secrets & ENC Best Practices”** for rotation, storage, and CI tips (download below).

---

## 🛡️ Production Guardrails
When the active profile is `prod`:
- If `logging.level` is missing or invalid → default to `INFO` with a warning.
- `logging.level: DEBUG` is **blocked** unless `allow_debug_in_prod: true` is present (in which case we log a warning).

Profiles `prod` and `test` **require** their respective `application-<profile>.yml`; otherwise load fails with a `ConfigLoadError`.

---

## 🔗 Imports
After the profile is merged into base, the loader processes:
```yaml
imports:
  - "features.yml"
  - "override.yml"
```
Missing files only warn; merge proceeds.

---

## 🧪 Testing & Debugging
```bash
pytest
pytest -m integration
```
If you use the test helper from this repo’s `tests/conftest.py`:
```bash
pytest --dump-config -s
```
This prints the merged config (with secrets redacted) from select tests.

To programmatically print a merged config yourself:
```python
import os, yaml
from sprigconfig import load_config

os.environ["APP_PROFILE"] = "dev"
cfg = load_config()
print(yaml.safe_dump(cfg, sort_keys=False))
```

---

## 🔧 Migration Note
- Remove `app.profile` from YAML files going forward. Runtime decides the profile and the loader injects it back into the final config.
- If you still have it in files, you’ll get a warning at startup.

---

## 📜 License
MIT
