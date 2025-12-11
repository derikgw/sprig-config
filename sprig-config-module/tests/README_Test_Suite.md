
# SprigConfig Test Suite  
**Location:** `sprig-config-module/tests/`  
**Purpose:** Validate the core configuration engine, secret-handling, deep-merge logic, profile overlays, import tracing, CLI behavior, and metadata propagation for SprigConfig.

This test suite is designed to be:

- **Deterministic** – reproducible across machines & CI  
- **Environment-aware** – driven by `APP_CONFIG_DIR`, `.env`, and pytest CLI flags  
- **Debug-friendly** – extensive logging & merged-config dumps  
- **Architecture-verifying** – tests import future public APIs (`ConfigLoader`, `Config`, `LazySecret`, etc.)  
- **High-coverage** – each subsystem has focused tests *plus* full integration routes  

---

# 🧱 Test Suite Structure

```
tests/
│
├── config/                   # Static test config tree used by many fixtures
├── test_logs/                # Log output generated automatically during testing
├── utils/                    # Test utilities, helpers, support modules
│
├── conftest.py               # Global fixtures, CLI flags, serialization helpers
├── conftest.md               # Documentation for conftest.py
│
├── test_cli.py               # Tests for CLI rendering, YAML dump, secret redaction
├── test_cli.md
│
├── test_config.py            # Tests for Config object, dotted-key lookup, immutability
├── test_config.md
│
├── test_config_singleton.py  # Tests for cached/global config singleton behavior
├── test_config_singleton.md
│
├── test_deep_merge.py        # Deep merge algorithm tests
├── test_deep_merge.md
│
├── test_import_trace.py      # Tests for recursive imports + detection of cycles
├── test_import_trace.md
│
├── test_integration.py       # End-to-end config loading with overlays, imports, meta
├── test_integration.md
│
├── test_meta.py              # Tests for _meta generation (sources, profile, trace)
├── test_meta.md
│
├── test_meta_sources.py      # Focused tests on metadata source annotations
├── test_meta_sources.md
│
├── test_profiles.py          # Profile overlay resolution, precedence, overrides
├── test_profile_behavior.md
│
└── .env                      # Optional test-time environment file
```

---

# 🔍 Overview of Technologies Used

### **1. Pytest**
Used for:

- Fixture dependency injection  
- Parameterized testing  
- CLI extension (`pytest_addoption`)  
- Conditional test skipping  

### **2. YAML + JSON Handling**
SprigConfig uses:

- `yaml.safe_load` / `safe_dump`  
- A custom deep merge implementation  
- Redaction and safe serialization wrappers  

### **3. Environment-Based Config Loading**
Tests validate:

- `APP_CONFIG_DIR` discovery  
- `.env` loading using python-dotenv  
- The `--env-path` override for test-time `.env` selection  

### **4. Secret Handling**
Using `LazySecret` with:

- Safe, redacted serialization  
- Optional secret resolution (`--dump-config-secrets`)  
- Optional plaintext dump (`--dump-config-no-redact`)  

### **5. Logging**
Full-session debug logs are produced:

```
test_logs/pytest_<timestamp>.log
```

containing:

- Trace-level diagnostics  
- Import maps  
- Merge order  
- File resolutions  

---

# 🚀 Pytest CLI Options (“Adoption Flags”)

These allow configurable behavior during test runs:

| Flag | Purpose |
|------|---------|
| `--env-path <file>` | Override which `.env` file tests use |
| `--dump-config` | Print merged config for each test |
| `--dump-config-format yaml|json` | Select print format |
| `--dump-config-secrets` | Resolve LazySecret values before printing |
| `--dump-config-no-redact` | Output plaintext secrets |
| `--debug-dump <file>` | Write merged config snapshot after test |
| `RUN_CRYPTO=true` | Run crypto-heavy tests |

---

# 🧪 Test Categories

## **1. Config Object & API**
`test_config.py`, `test_config_singleton.py`

Ensures:

- Dotted-key lookup  
- Deep copying  
- Immutability guarantees  
- Consistent `.to_dict()` round-tripping  

---

## **2. Deep Merge Algorithm**
`test_deep_merge.py`

Validates:

- Overlays  
- Replacement semantics  
- Collision rules  
- Recursive merge behavior  

---

## **3. Import Tracing**
`test_import_trace.py`

Ensures:

- Recursive file imports  
- Cycle detection  
- Metadata chain-building  

---

## **4. Profiles (application-<profile>.yml)**
`test_profiles.py`

Covers:

- File precedence  
- Profile inheritance  
- Environment-driven selection  

---

## **5. Metadata Plumbing**
`test_meta.py`, `test_meta_sources.py`

Ensures:

- Source tracking  
- Import trace awareness  
- Storage in:  
  ```
  sprigconfig._meta
  ```

---

## **6. CLI Behavior**
`test_cli.py` validates:

- Pretty YAML output  
- Redacted vs resolved secret output  
- CLI error messaging  

---

## **7. Full Integration Tests**
`test_integration.py`

Simulates:

- Real config directory  
- Overlays  
- Imports  
- Metadata  
- LazySecret injection  
- Environment discovery  

This is the closest to real runtime behavior.

---

# 🔧 Running the Test Suite

Run all tests:

```
pytest
```

Enable debug logging + see merged configs:

```
pytest --dump-config
```

Use a custom `.env` file:

```
pytest --env-path=tests/.env.dev
```

Capture merged config snapshots:

```
pytest --debug-dump=/tmp/config.yml
```

Run crypto tests:

```
RUN_CRYPTO=true pytest
```

---

# 🧩 Adding New Tests

Follow this pattern:

1. Create a `.py` test file  
2. Create a `.md` file with the same name (optional but recommended)  
3. If tests need a config tree:  
   - Use `full_config_dir` or  
   - Create a temporary directory  
4. If coverage touches import or overlay behavior, include:  
   ```
   cfg = capture_config(lambda: ConfigLoader(...).load())
   ```  
   This ensures `.yml` snapshots can be captured.

---

# 📎 Notes

- **Do not** modify `tests/config/` during tests — use `full_config_dir` instead.  
- All `.md` files in the test suite are **developer documentation**, not used by pytest.  
- `conftest.py` is the authoritative specification of test mechanics.  

---

# ✔️ Final Thoughts

SprigConfig’s test suite is intentionally *dense* and *diagnostic-rich*.  
It exists not just to assert correctness, but to illuminate exactly:

- how configs merge  
- where imports originate  
- how metadata propagates  
- how environment variables influence resolution  
- and how secrets are safely handled  

This ensures the configuration engine remains predictable, secure, and transparent — even as the architecture evolves.

