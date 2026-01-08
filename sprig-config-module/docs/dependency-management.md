# Dependency Management

This document describes how to manage Python dependencies in the SprigConfig project using Poetry.

## Table of Contents

- [Viewing Dependencies](#viewing-dependencies)
- [Understanding Dependency Trees](#understanding-dependency-trees)
- [Finding Why a Package is Installed](#finding-why-a-package-is-installed)
- [Updating Dependencies](#updating-dependencies)
- [Security Scanning](#security-scanning)
- [Best Practices](#best-practices)

---

## Viewing Dependencies

### List All Installed Packages

```bash
cd sprig-config-module

# List all dependencies with versions
poetry show

# List only direct dependencies (from pyproject.toml)
poetry show --only main
poetry show --only dev

# List with short descriptions
poetry show --all
```

### View Specific Package Details

```bash
# Show details for a specific package (like "yarn why")
poetry show <package-name>

# Example: Find who depends on urllib3
poetry show urllib3
```

**Example Output:**
```
name         : urllib3
version      : 2.6.2
description  : HTTP library with thread-safe connection pooling

required by
 - requests >=1.21.1,<3
 - pip-audit *
```

---

## Understanding Dependency Trees

### View Full Dependency Tree

```bash
# Show complete dependency tree
poetry show --tree

# Show tree for specific dependency group
poetry show --tree --only main
poetry show --tree --only dev
```

**Example Output:**
```
cryptography 46.0.1
├── cffi >=1.12
│   └── pycparser *
└── ...

requests 2.32.3
├── charset-normalizer >=2,<4
├── idna >=2.5,<4
├── urllib3 >=1.21.1,<3
└── certifi >=2017.4.17
```

### Find Dependencies of a Specific Package

```bash
# Show what a package depends on
poetry show <package-name> --tree

# Example: What does cryptography depend on?
poetry show cryptography --tree
```

### Find What Depends on a Package

```bash
# Use grep to find reverse dependencies
poetry show --tree | grep -B 5 <package-name>

# Example: What packages depend on urllib3?
poetry show --tree | grep -B 5 urllib3
```

---

## Finding Why a Package is Installed

When you discover a package you didn't explicitly add (like `urllib3`), use these commands to understand the dependency chain:

### Method 1: Direct Query

```bash
# Show package info including "required by"
poetry show urllib3
```

This shows which packages directly depend on it.

### Method 2: Reverse Search in Tree

```bash
# Find all dependency paths leading to the package
poetry show --tree | grep -B 10 urllib3
```

### Method 3: Check Lock File

```bash
# Search poetry.lock for dependency information
grep -A 20 "name = \"urllib3\"" poetry.lock
```

---

## Updating Dependencies

### Update a Specific Package

```bash
# Update a single package to latest compatible version
poetry update <package-name>

# Example: Update urllib3 to fix CVE
poetry update urllib3
```

### Update a Parent Package (and Its Dependencies)

```bash
# Update a parent package (like requests), which will update its dependencies
poetry update requests

# This will also update urllib3 if requests requires a newer version
```

### Update All Dependencies

```bash
# Update all packages to their latest compatible versions
poetry update

# Update only main dependencies (not dev)
poetry update --only main

# Update only dev dependencies
poetry update --only dev
```

### Update to Latest Versions (Ignoring Constraints)

```bash
# Check what updates are available
poetry show --outdated

# Update a package to the absolute latest (may break compatibility)
# Edit pyproject.toml to change version constraint, then:
poetry lock --no-update
poetry install
```

### Dry Run (See What Would Be Updated)

```bash
# See what would be updated without making changes
poetry update --dry-run
```

---

## Security Scanning

SprigConfig uses **pip-audit** for vulnerability scanning (official PyPA tool).

### Run Security Scan Locally

```bash
cd sprig-config-module

# Basic vulnerability scan
poetry run pip-audit

# Generate JSON report
poetry run pip-audit --format json --output pip-audit-report.json

# Show detailed vulnerability descriptions
poetry run pip-audit --desc

# Attempt to automatically fix vulnerabilities
poetry run pip-audit --fix
```

### Understanding pip-audit Output

```
Found 1 known vulnerability in 1 package
Name    Version ID             Fix Versions
------- ------- -------------- ------------
urllib3 2.6.2   CVE-2026-21441 2.6.3
```

- **Name**: Package with vulnerability
- **Version**: Currently installed version
- **ID**: CVE identifier
- **Fix Versions**: Version(s) that fix the vulnerability

### Fixing Security Vulnerabilities

**Option 1: Update the vulnerable package directly**
```bash
poetry update urllib3
```

**Option 2: Update the parent package**
```bash
# If urllib3 is required by requests
poetry update requests
```

**Option 3: Use pip-audit's auto-fix**
```bash
poetry run pip-audit --fix
```

**Option 4: Manual version pinning**
```bash
# Edit pyproject.toml to add explicit constraint
# [tool.poetry.dependencies]
# urllib3 = ">=2.6.3"

poetry update urllib3
```

### Security Scanning in CI/CD

pip-audit runs automatically in GitLab CI during the `security` stage:

```yaml
pip_audit:
  stage: security
  script:
    - pip install pip-audit
    - pip-audit --format json --output pip-audit-report.json
```

### Pre-commit Hooks

pip-audit also runs on every commit (non-blocking):

```bash
# Run manually
poetry run pre-commit run pip-audit

# Runs automatically on git commit
git commit -m "your changes"
```

---

## Best Practices

### 1. Regular Dependency Updates

```bash
# Monthly: Check for outdated packages
poetry show --outdated

# Update dev dependencies regularly
poetry update --only dev

# Update main dependencies with caution (test thoroughly)
poetry update --only main
```

### 2. Security-First Updates

```bash
# Weekly: Run security scan
poetry run pip-audit

# Address high-severity CVEs immediately
poetry update <vulnerable-package>
```

### 3. Understand Before Updating

```bash
# Before updating, understand the dependency chain
poetry show <package-name>
poetry show --tree | grep <package-name>

# Check changelog for breaking changes
# Visit package repository or PyPI page
```

### 4. Test After Updates

```bash
# After any dependency update, run full test suite
poetry run pytest

# Run linting
poetry run ruff check src

# Run security scans
poetry run bandit -r src
poetry run pip-audit
```

### 5. Lock File Hygiene

```bash
# Commit poetry.lock after dependency changes
git add poetry.lock pyproject.toml
git commit -m "chore: update dependencies"

# Never edit poetry.lock manually
# Always use poetry commands to modify dependencies
```

### 6. Transitive Dependency Issues

If you need to force an update of a transitive dependency (like urllib3):

**Option A: Add explicit constraint**
```toml
[tool.poetry.dependencies]
urllib3 = ">=2.6.3"  # Override transitive requirement
```

**Option B: Update parent packages**
```bash
# Update all packages that depend on urllib3
poetry update requests cryptography pip-audit
```

### 7. Monorepo Considerations

This is a monorepo with two Poetry projects:
- `sprig-config-module/` (main project)
- `sprig-tools/` (developer utilities)

Manage dependencies separately:
```bash
# Update sprig-config-module
cd sprig-config-module
poetry update

# Update sprig-tools
cd ../sprig-tools
poetry update
```

---

## Common Workflows

### "I found a CVE in the pipeline. How do I fix it?"

1. Identify the vulnerable package from pip-audit output
2. Check what depends on it:
   ```bash
   poetry show <vulnerable-package>
   ```
3. Update it:
   ```bash
   poetry update <vulnerable-package>
   ```
4. If that doesn't work, update parent packages:
   ```bash
   poetry update <parent-package>
   ```
5. Test:
   ```bash
   poetry run pytest
   poetry run pip-audit  # Verify fix
   ```
6. Commit:
   ```bash
   git add poetry.lock
   git commit -m "security: update <package> to fix CVE-XXXX-XXXXX"
   ```

### "Why is this package installed? I didn't add it."

```bash
# Find out what depends on it
poetry show <package-name>

# See full dependency chain
poetry show --tree | grep -B 10 <package-name>
```

### "I want to update everything safely"

```bash
# Check what's outdated
poetry show --outdated

# Update dev dependencies (lower risk)
poetry update --only dev
poetry run pytest

# Update main dependencies (higher risk - test thoroughly)
poetry update --only main
poetry run pytest
poetry run pip-audit
```

---

## Related Documentation

- [CONTRIBUTING.md](../CONTRIBUTING.md) - General contribution guidelines
- [Poetry Documentation](https://python-poetry.org/docs/) - Official Poetry docs
- [pip-audit Documentation](https://github.com/pypa/pip-audit) - Security scanning tool

---

## Quick Reference

| Task | Command |
|------|---------|
| List all packages | `poetry show` |
| Show package details | `poetry show <package>` |
| View dependency tree | `poetry show --tree` |
| Check outdated packages | `poetry show --outdated` |
| Update one package | `poetry update <package>` |
| Update all packages | `poetry update` |
| Security scan | `poetry run pip-audit` |
| Fix vulnerabilities | `poetry run pip-audit --fix` |
| Pre-commit scan | `poetry run pre-commit run --all-files` |
