# SprigConfig – Developer Guide

This guide is intended for **developers and contributors working on SprigConfig itself**. It covers repository structure, local development setup, testing, Git workflows, CI/CD processes, dependency management, and release procedures.

If you're a **user** of SprigConfig, see the [main documentation index](index.md) instead.

---

## 🚀 Quick Start for Contributors

### Local Development Setup

SprigConfig uses Poetry for dependency management. The main project is in `sprig-config-module/`:

```bash
cd sprig-config-module

# Install dependencies (including dev tools)
poetry install

# Activate the virtual environment
poetry shell
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov=src --cov-report=xml

# Run specific test file
poetry run pytest tests/test_config_loader.py

# Run single test function
poetry run pytest tests/test_config_loader.py::test_function_name

# Exclude integration tests (faster for quick feedback)
poetry run pytest -m "not integration"

# Exclude crypto tests (don't require APP_SECRET_KEY)
poetry run pytest -m "not crypto"

# Enable crypto tests (requires APP_SECRET_KEY env var)
RUN_CRYPTO=true poetry run pytest
```

### Code Quality

```bash
# Lint with ruff
poetry run ruff check src

# Format code (if ruff has format support)
poetry run ruff format src
```

---

## 📚 Documentation for Contributors

### Understanding the Codebase

- **[Dependency Injection - Implementation Explained](dependency-injection-explained.md)** — How ConfigValue and @ConfigurationProperties work
- **[Configuration Injection Guide](configuration-injection.md)** — Detailed patterns for config injection
- **[Dependency Management](dependency-management.md)** — Managing dependencies with Poetry, vendoring, etc.

### Secrets & Security

- **[Secrets & ENC() Best Practices](SprigConfig_ENC_BestPractices.md)** — Key generation, encryption, and operational security

### Git & Version Control

- **[Test config files & git skip-worktree](git_skip_worktree_for_test_config_files.md)** — Git workflows for test configuration files

### Release & Deployment

- **[Release Checklist](release_checklist.md)** — Step-by-step process for releasing new versions
- **[GitLab CI/CD Pipeline](GitLab.md)** — Understanding the automated testing and deployment pipeline
- **[PyPI Publishing](PyPI.md)** — Publishing packages to PyPI

GitHub Actions now provides phased workflows in `.github/workflows/ci.yml`,
`.github/workflows/security.yml`, `.github/workflows/release-checks.yml`, and
`.github/workflows/manual-publish.yml`. During the migration, GitLab Pages remains on GitLab,
while GitHub Actions now mirrors dependency scanning, Bandit SAST, gitleaks secret detection,
and offers a manual publishing path for TestPyPI and PyPI.

### Documentation

- **[Building Documentation](building_documentation.md)** — Building, previewing, and deploying these docs with MkDocs

---

## 🏗️ Repository Structure

```
sprig-config-module/
├── src/sprigconfig/              # Main library source
│   ├── config_loader.py          # Configuration loading & merging
│   ├── config.py                 # Config class (dict-like interface)
│   ├── lazy_secret.py            # LazySecret for encrypted values
│   ├── deepmerge.py              # Deep merge algorithm
│   ├── exceptions.py             # Custom exceptions
│   ├── config_singleton.py       # Thread-safe cached loader
│   └── cli.py                    # Command-line interface
├── tests/                        # Test suite
│   ├── conftest.py              # Shared fixtures & test infrastructure
│   ├── config/                  # Test configuration files (YAML)
│   └── test_*.py                # Test modules
├── docs/                         # GitHub Pages documentation
│   ├── index.md                 # Documentation home (you are here)
│   └── *.md                     # Various guides
├── pyproject.toml               # Project metadata, dependencies, build
├── mkdocs.yml                   # MkDocs configuration
└── README.md                    # User-facing README
```

---

## 🔀 Deep Merge Semantics

SprigConfig uses a **deterministic deep merge algorithm** to combine configuration layers. Understanding this behavior is essential for both users and contributors.

### Merge Rules

| Type | Behavior |
|------|----------|
| **Dictionaries** | Recursively merged — keys from both layers are combined, nested dicts merge deeply |
| **Lists** | Overwrite — the overlay completely replaces the base list (no append) |
| **Scalars** | Overwrite — later values override earlier ones |

### Example

**Base configuration** (`application.yml`):
```yaml
server:
  port: 8080
  host: localhost
  timeout: 30
features:
  - auth
  - logging
```

**Profile overlay** (`application-dev.yml`):
```yaml
server:
  port: 9090
  debug: true
features:
  - mock-auth
```

**Merged result**:
```yaml
server:
  port: 9090      # overwritten by overlay
  host: localhost # preserved from base (deep merge)
  timeout: 30     # preserved from base
  debug: true     # added by overlay
features:
  - mock-auth     # replaced entirely (lists don't append)
```

### Collision Warnings

When an overlay **partially overrides** a section (some keys present, others missing), SprigConfig logs a warning. This helps catch unintentional omissions:

```
WARNING sprigconfig.deepmerge: Config section 'server' partially overridden; missing keys: {'timeout', 'host'}
```

This warning indicates the overlay touched the `server` section but didn't include all keys from the base — which may be intentional (override specific values) or a mistake (forgot to include keys).

### Merge Order

Configuration is merged in this order:

1. `application.yml` (base)
2. Imports from base (in declared order)
3. `application-<profile>.yml` (profile overlay)
4. Imports from profile overlay (in declared order)

Later sources override earlier ones. The full merge order is recorded in `sprigconfig._meta.sources` for debugging.

### Implementation

The deep merge logic lives in `src/sprigconfig/deepmerge.py`. Key behaviors:

- Recursive descent into nested dictionaries
- Non-dict values (including lists) replace rather than merge
- Collision detection compares keys between base and overlay sections
- All merge operations are logged at DEBUG level for traceability

---

## 🧪 Testing Architecture

Each test module (`test_*.py`) has a paired markdown file (`test_*.md`) explaining its design.

**Key test fixtures** (in `tests/conftest.py`):
- `config` — Loaded test configuration
- `config_dir` — Path to test config directory
- `app_secret_key` — Fernet key for crypto tests

**Test categories:**
- Configuration mechanics (loading, merging, override behavior)
- Metadata tracking and provenance
- Deep merge semantics
- Profile overlay behavior
- LazySecret and encryption
- CLI functionality
- Integration tests

For details on the test framework, see `tests/conftest.md`.

---

## 🔄 Git Workflow

1. **Create feature branch** from `main`:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes** and ensure tests pass:
   ```bash
   poetry run pytest
   ```

3. **Commit with clear messages**:
   ```bash
   git commit -m "feat: add new feature" -m "Description of changes"
   ```

4. **Push and create a pull request** to `main`

5. **CI runs automatically** (lint, tests, security scans)

6. **After merge**, maintainers prepare release (see [Release Checklist](release_checklist.md))

---

## 📦 Dependency Management

- **Poetry** manages all dependencies (see [pyproject.toml](../pyproject.toml))
- **Python 3.11+** required
- Key dependencies:
  - `PyYAML` ≥6.0.2 — YAML parsing
  - `cryptography` ^46.0.7 — Fernet encryption
  - `python-dotenv` — .env file support (dev)

See **[Dependency Management](dependency-management.md)** for vendor strategies and best practices.

---

## 🚀 Release Process

For releasing new versions, follow the **[Release Checklist](release_checklist.md)**:

1. **Prep**: Verify tests pass, update version, update CHANGELOG
2. **Build**: Create wheel and sdist artifacts
3. **Tag**: Create annotated git tag
4. **CI/CD**: Monitor GitHub validation and publish runs plus any remaining GitLab release jobs, confirm uploads to the intended registry
5. **Post-release**: Verify installation, announce release

---

## 🔐 Security & Encryption

SprigConfig handles encrypted configuration values using **Fernet** (from `cryptography` package).

Key points:
- Use `APP_SECRET_KEY` environment variable for the Fernet key
- Never commit keys to source control
- Secrets are stored as `ENC(...)` in YAML
- LazySecret decrypts values only when accessed
- See **[Secrets & ENC() Best Practices](SprigConfig_ENC_BestPractices.md)** for full guidelines

---

## 📝 Version Control Notes

### Skip-Worktree for Test Configs

Test configuration files may contain sensitive values (even though they're encrypted). Use `git skip-worktree` to prevent accidental commits of modified test configs:

```bash
git update-index --skip-worktree tests/config/application-secrets.yml
git ls-files -v | grep ^S  # Check skip-worktree status
```

See **[git skip-worktree guide](git_skip_worktree_for_test_config_files.md)** for details.

---

## 🔍 Debugging & Troubleshooting

### Check Current Version

```bash
python -c "import sprigconfig; print(sprigconfig.__version__)"
```

### Debug Configuration Loading

Use pytest flags to inspect merged config:
```bash
poetry run pytest --dump-config --dump-config-format=yaml tests/test_something.py
poetry run pytest --dump-config-secrets --dump-config-no-redact tests/test_something.py
```

### No Module Named 'sprigconfig'

Ensure:
1. You're in the `sprig-config-module/` directory
2. Poetry installed packages: `poetry install`
3. Running with Poetry: `poetry run python ...` or `poetry shell` first

---

## 🤝 Contributing Guidelines

- Follow existing code patterns and naming conventions
- Write tests for new features
- Ensure all tests pass before submitting PRs
- Update documentation and CHANGELOG
- See [CONTRIBUTING.md](../CONTRIBUTING.md) for full guidelines

---

## 📚 Additional Resources

- **[Main Documentation Index](index.md)** — All documentation
- **[CHANGELOG.md](../CHANGELOG.md)** — Version history
- **[ROADMAP.md](../ROADMAP.md)** — Future plans
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** — General contribution guidelines
- **[PyPI Package](https://pypi.org/project/sprigconfig/)** — Published package

---

## ❓ Need Help?

- 📖 Check relevant guide in this folder
- 🧪 Look at test examples in `tests/`
- 🐛 Open an issue on GitHub for bugs/features
- 💬 Discuss in GitHub Discussions for questions
