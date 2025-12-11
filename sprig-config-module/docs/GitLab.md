
# SprigConfig GitLab CI Pipeline Documentation

This document explains the CI/CD pipeline defined in `.gitlab-ci.yml` for the **SprigConfig** project.
It covers the purpose of each job, how version-controlled publishing works, required authentication,
and how GitLab’s Package Registry integrates with Poetry-based publishing.

---

# 📌 Overview of the CI Pipeline

The CI pipeline is designed to:

- Perform linting and formatting checks
- Run unit tests with coverage
- Execute security scans (SAST + Secret Detection)
- Build and publish the SprigConfig package to GitLab’s internal PyPI registry
- Enforce strict version/tag consistency
- Require manual approval before publishing

The pipeline runs using `python:3.13-slim` and installs Poetry 2.2.x on each job.

---

# 🧱 Pipeline Structure

```
stages:
  - lint
  - test
  - security
  - deploy
```

Each stage corresponds to a logical phase of quality and deployment.

All jobs inherit from:

```
.default_setup:
  image: python:3.13-slim
  before_script:
    - cd sprig-config-module
    - pip install poetry==2.2.0
    - poetry install
```

This ensures consistent tooling across jobs.

---

# 🔎 Workflow Rules

The pipeline runs on:

- **Any commit to any branch**
- **Any tag pushed to the repository**

Manual deploy jobs run **only on version tags** (`v1.2.0`, `V0.1.9`, etc.).

---

# 🧹 Lint Stage

Job: `lint`

Purpose: Verify style and best practices using Ruff.

```
poetry run ruff check src
```

Artifacts include `ruff.log` for offline review.

---

# 🧪 Test Stage

Job: `pytest`

Features:

- Runs full unit test suite
- Coverage via `pytest-cov`
- Injects a known test Fernet key (`APP_SECRET_KEY`) for `LazySecret` tests
- Produces coverage + JUnit reports for GitLab UI

Artifacts include:

- `coverage.xml`
- JUnit test reports
- Logs from tests

---

# 🔒 Security Stage

Two GitLab-provided scanners run automatically:

- **SAST** (Static Application Security Testing)
- **Secret Detection**

These use GitLab’s security templates and require no additional configuration.

---

# 🚀 Deploy Stage (Manual)

There are **two deployment jobs**, both manual:

---

## 1️⃣ `dry_run_pypi`

Purpose:

- Ensures the project can *build* successfully
- Ensures version tags match `pyproject.toml`
- Performs a `poetry publish --dry-run`
- Does **not** upload the package

Version check logic:

```
pyproject version = poetry version -s
tag version = CI_COMMIT_TAG (stripped of v/V)
```

If they differ → job fails.

Artifacts include the `dist/` directory.

---

## 2️⃣ `deploy_pypi`

Runs only after:

- `dry_run_pypi` succeeded
- Manual approval is given

This job performs the actual publish:

```
poetry publish --no-interaction -r gitlab-pypi
```

This uploads the wheel + sdist to the GitLab Package Registry.

---

# 🔑 Authentication Requirements

The CI pipeline uses environment variables:

```
GITLAB_PYPI_TOKEN    # must have write_registry scope
POETRY_HTTP_BASIC_GITLAB_PYPI_USERNAME="__token__"
POETRY_HTTP_BASIC_GITLAB_PYPI_PASSWORD=$GITLAB_PYPI_TOKEN
```

This is the official pattern for authenticated PyPI publishing.

---

# 🏷️ Tagging Rules (Strict)

A tag triggers the deploy pipeline **only if**:

- It starts with `v` or `V`
- It matches `pyproject.toml` version (after removing leading v/V)
- It is pushed to GitLab

Examples:

| Tag pushed | pyproject version | Allowed? | Reason |
|-----------|-------------------|----------|--------|
| `v1.2.0` | `1.2.0` | ✔️ | Correct |
| `V2.0.1` | `2.0.1` | ✔️ | Correct |
| `1.0.0` | `1.0.0` | ❌ | Must start with v/V |
| `v1.1` | `1.1.5` | ❌ | Version mismatch |

---

# 📦 Package Registry Information

The registry URL appears in `pyproject.toml`:

```
[[tool.poetry.source]]
name = "gitlab-pypi"
url = "https://gitlab.tsod.ad.usmc.mil/api/v4/projects/<project-id>/packages/pypi"
priority = "supplemental"
```

Poetry uses this when running:

```
poetry publish -r gitlab-pypi
```

---

# 🧭 Summary

The SprigConfig CI pipeline guarantees:

- Consistent Python + Poetry environment
- Automatic linting, testing, and scanning
- Strict version consistency between tags and published builds
- Safety through dry-run publishing
- Manual confirmation before releasing
- Secure deployment using GitLab's registry and tokens

This ensures that all published versions are safe, validated, and traceable.

