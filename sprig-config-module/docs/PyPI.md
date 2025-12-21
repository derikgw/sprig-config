
# SprigConfig Packaging & GitLab PyPI Publishing

This document explains how SprigConfig is packaged, versioned, and published to the
GitLab Package Registry using Poetry and GitLab CI pipelines.

---

# 📦 Packaging Overview

SprigConfig uses **Poetry 2.2.x** as its build and dependency manager.

Running:

```
poetry build
```

creates:

```
dist/
  sprigconfig-<version>.tar.gz
  sprigconfig-<version>-py3-none-any.whl
```

This is reproducible thanks to deterministic builds and pinned dependencies.

---

# 🏗️ Local Build Instructions

To build locally:

```
cd sprig-config-module
poetry install
poetry build
```

No additional steps are required. Poetry handles building:

- Wheel  
- Source distribution (sdist)  

---

# 🔑 Authentication for Publishing

Publishing requires:

- A GitLab **project** or **group token**
- Token must have: `write_registry`

Environment variables:

```
POETRY_HTTP_BASIC_GITLAB_PYPI_USERNAME="__token__"
POETRY_HTTP_BASIC_GITLAB_PYPI_PASSWORD="$GITLAB_PYPI_TOKEN"
```

These instruct Poetry how to authenticate to GitLab’s registry.

You can test auth locally:

```
poetry publish --dry-run -r gitlab-pypi
```

---

# 🧭 Registry Configuration in pyproject.toml

```
[[tool.poetry.source]]
name = "gitlab-pypi"
url = "https://gitlab.tsod.ad.usmc.mil/api/v4/projects/<project-id>/packages/pypi"
priority = "supplemental"
```

Details:

- PyPI.org remains the primary source  
- GitLab registry is supplemental  
- Builds publish *only* to GitLab registry  

---

# 🏷️ Versioning Workflow

Version is set using:

```
poetry version patch
poetry version minor
poetry version major
```

Or manually:

```
poetry version 1.5.2
```

This updates:

- `pyproject.toml`
- internal version metadata

Git tags must match these versions.

---

# 🚀 Publishing Workflow (via CI)

Publishing is performed only by GitLab CI, not manually.

### 1️⃣ Developer pushes a version tag

```
git tag v1.2.0
git push --tags
```

### 2️⃣ CI runs `dry_run_pypi`

- Ensures tag matches version  
- Builds the package  
- Runs a simulated publish  

### 3️⃣ CI runs `deploy_pypi` (manual approval)

- Performs a real `poetry publish`  
- Uploads artifacts to GitLab’s registry  

This ensures:

- Reproducible publishing  
- No accidental uploads  
- Manual human approval  

---

# 📥 Consuming SprigConfig from GitLab PyPI

Add this to the consumer project's `pyproject.toml`:

```
[[tool.poetry.source]]
name = "sprigconfig-internal"
url = "https://gitlab.tsod.ad.usmc.mil/api/v4/projects/<project-id>/packages/pypi"
priority = "supplemental"
```

Then:

```
poetry add sprig-config
```

---

# 🧪 Troubleshooting

### ❌ 401 Unauthorized  
Token missing or lacking `write_registry`.

### ❌ version mismatch  
Tag does not match Poetry version.

### ❌ registry not found  
Incorrect project ID in source URL.

### ❌ failed to build  
Re-run locally:

```
poetry build -vvv
```

---

# ✔️ Summary

SprigConfig’s packaging is:

- Poetry-driven  
- Deterministic  
- Enforced by CI  
- Safe (dry-run first)  
- Published only on valid version tags  
- Hosted entirely in GitLab’s internal registry  

This makes SprigConfig easy to distribute, version, and integrate into other systems across the organization.
