# 🌱 SprigConfig

[![PyPI version](https://img.shields.io/pypi/v/sprig-config.svg)](https://pypi.org/project/sprig-config/)
[![Security Scan](https://img.shields.io/badge/security-monitored-brightgreen)](https://sprig-config-7f4835.gitlab.io/)

SprigConfig is a lightweight, opinionated configuration system for Python
applications. It provides layered YAML loading, profile overlays, environment
variable expansion, recursive imports, safe secret handling, and detailed metadata
tracking designed for clarity, reproducibility, and debuggability.

This updated README reflects the current, expanded architecture of SprigConfig —
including its test infrastructure, `.env` handling model, and secret‑management APIs.

---

# ⭐ Key Features

### ✔️ Profile Injection (Runtime-Driven)
Profiles are *never* taken from files. The active profile comes from:

1. `load_config(profile=...)`  
2. `APP_PROFILE`  
3. `pytest` → `"test"`  
4. Otherwise → `"dev"`

Injected into final config as:

```yaml
app:
  profile: <active>
```

If a YAML file contains `app.profile`, it is ignored with a warning.

---

### ✔️ Layered YAML Merging (Deep Merge)
SprigConfig merges:

1. `application.yml`
2. `application-<profile>.yml`
3. `imports: [file1.yml, file2.yml, …]`

Features include:

- Recursive dictionary merging  
- Override collision warnings  
- Partial merge clarity  
- Preservation of source metadata

---

### ✔️ Environment Variable Expansion
Patterns:

```
${VAR}
${VAR:default}
```

Expanded at load time. Missing variables fall back to defaults.

---

### ✔️ Secure Secret Handling
Values formatted as:

```
ENC(<ciphertext>)
```

are mapped to `LazySecret` objects.

- Decryption is lazy (on `.get()`)  
- Uses global Fernet key via `APP_SECRET_KEY`  
- Supports global key providers  
- Secrets redacted during dumps unless explicitly allowed  

---

### ✔️ Dependency Injection

Spring Boot-style dependency injection for cleaner code. Bind config values using descriptors and decorators instead of explicit `Config.get()` calls:

**Field-Level Binding:**
```python
from sprigconfig import ConfigValue

class MyService:
    db_url: str = ConfigValue("database.url")
    timeout: int = ConfigValue("service.timeout", default=30)
    api_key: str = ConfigValue("api.key", decrypt=True)

service = MyService()
print(service.db_url)  # Resolved from config
```

**Class-Level Binding:**
```python
from sprigconfig import ConfigurationProperties

@ConfigurationProperties(prefix="database")
class DatabaseConfig:
    url: str
    port: int
    username: str

db = DatabaseConfig()
print(db.url)  # Auto-bound from config["database"]["url"]
```

**Function Parameter Injection:**
```python
from sprigconfig import config_inject

@config_inject
def connect_db(
    host: str = ConfigValue("database.host"),
    port: int = ConfigValue("database.port", default=5432)
):
    return connect(host, port)

connect_db()  # Uses config values
connect_db(host="override")  # Override specific params
```

**Features:**
- Type conversion based on type hints (int, float, bool, str, list, dict)
- LazySecret handling with configurable `decrypt` parameter
- Nested object auto-binding
- Clear error messages with full context

See [Dependency Injection Explained](docs/dependency-injection-explained.md) for implementation details.

---

### ✔️ Import Chains
Inside any YAML file:

```yaml
imports:
  - features.yml
  - security.yml
```

SprigConfig resolves imports relative to `APP_CONFIG_DIR` or the config root
and detects circular imports.

---

### ✔️ Metadata Injection
Every loaded config includes:

```
sprigconfig._meta:
  profile: <active>
  sources: [list of resolved files]
  import_trace: <graph of import relationships>
```

This helps debugging and auditing.

---

### ✔️ BOM-Safe YAML Reads
UTF‑8 with BOM (`utf-8-sig`) is automatically sanitized so Windows-created
files don’t introduce odd keys like `ï»¿server`.

---

# 📦 Installation

```bash
pip install sprig-config
# or
poetry add sprig-config
```

---

# 📁 Project Structure

```
sprigconfig/
    config_loader.py
    config.py
    lazy_secret.py
    deepmerge.py
    exceptions.py
    ...

docs/
    README_AI_Info.md
    (future docs go here)

tests/
    conftest.py
    conftest.md
    test_*.py
    test_*.md
    config/
```

### Documentation Strategy
- **docs/** → Project-wide documentation (AI disclosure, architecture notes)
- **tests/** → Each test module has matching `.md` explaining its purpose
- **conftest.md** → Documentation for the test framework itself  

This ensures the entire system is self-explaining.

---

# 📂 Configuration Layout Example

```
config/
  application.yml
  application-dev.yml
  application-test.yml
  application-prod.yml
  features.yml
  override.yml
```

### `application.yml`

```yaml
server:
  port: 8080
logging:
  level: INFO
```

### `application-dev.yml`

```yaml
server:
  port: 9090
imports:
  - features.yml
  - override.yml
```

### `override.yml`

```yaml
server:
  port: 9999
features:
  auth:
    methods: ["password", "oauth"]
```

---

# ⚙️ Runtime Selection & Profile Behavior

SprigConfig determines profile → merges → injects profile → processes imports.

```python
from sprigconfig import load_config

cfg = load_config(profile="dev")
print(cfg["server"]["port"])  # 9999
print(cfg["app"]["profile"])  # dev
```

---

# 🔐 Secret Handling with `LazySecret`

```yaml
secrets:
  db_user: ENC(gAAAAA...)
  db_pass: ENC(gAAAAA...)
```

```python
val = cfg["secrets"]["db_pass"]
assert isinstance(val, LazySecret)
print(val.get())  # plaintext
```

LazySecrets are:

- Safe by default  
- Not decrypted unless `.get()` is called  
- Redacted in dumps  

---

# 📜 `.env` Resolution Model

SprigConfig supports configuration directory override via:

1. `load_config(config_dir=...)`
2. `APP_CONFIG_DIR`
3. `.env` in the project root
4. Test overrides (`--env-path`)
5. Default: `./config`

### `.env` example:

```
APP_CONFIG_DIR=/opt/myapp/config
APP_SECRET_KEY=AbCdEf123...
```

---

# 🧪 Test Suite Overview

SprigConfig has a **documented, extensible test architecture**.

### Test categories:
- Config mechanics  
- Metadata & import tracing  
- Deep merge  
- Profile overlay behavior  
- LazySecret & crypto handling  
- CLI serialization tests  
- Integration tests with full directory copies  

### Documentation-per-test:
Every test module includes a paired `.md` file explaining its purpose and architecture.

---

# 🧰 Test CLI Flags (from `conftest.py`)

| Flag | Purpose |
|------|---------|
| `--env-path` | Use a custom `.env` file during tests |
| `--dump-config` | Print merged config for debugging |
| `--dump-config-format yaml|json` | Output format |
| `--dump-config-secrets` | Resolve LazySecrets |
| `--dump-config-no-redact` | Show plaintext secrets |
| `--debug-dump=file.yml` | Write merged config snapshot |
| `RUN_CRYPTO=true` | Enable crypto-heavy tests |

These make the test suite extremely reproducible and transparent.

---

# 🛡️ Production Guardrails

When profile = `prod`:

- Missing `logging.level` → default to `INFO`  
- `logging.level: DEBUG` blocked unless  
  ```
  allow_debug_in_prod: true
  ```
- Missing `application-prod.yml` → error  
- Missing `application-test.yml` (when test) → error  

---

# 🔗 Programmatic Access

```python
from pathlib import Path
from sprigconfig import ConfigLoader

loader = ConfigLoader(config_dir=Path("config"), profile="dev")
cfg = loader.load()

print(cfg.get("server.port"))
print(cfg.to_dict())
```

---

# 🧭 Migration Notes

- Remove `app.profile` from YAML files; runtime decides profile  
- Use imports for modularizing config trees  
- Secrets should always be stored as encrypted `ENC(...)` values  

---

## Versioning

SprigConfig follows [Semantic Versioning](https://semver.org/):

- **MAJOR** versions introduce breaking changes
- **MINOR** versions add backward-compatible functionality
- **PATCH** versions contain backward-compatible bug fixes

Pre-release versions (e.g. `-rc1`) indicate a release candidate.
They are feature-complete but may receive final fixes before a stable release
and are not recommended for production use unless explicitly intended for testing.

# 📚 Additional Documentation

Developer-focused documentation is available under the `docs/` directory:

- 📘 [Developer Guide](docs/README_Developer_Guide.md)
- 🧭 [Roadmap](ROADMAP.md)
- 📝 [Changelog](CHANGELOG.md)

These documents cover contributor workflows, test mechanics, Git usage,
CI/release processes, and internal design notes.

# 📄 License

MIT
