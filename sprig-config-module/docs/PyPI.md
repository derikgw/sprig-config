
# SprigConfig Packaging & Registry Publishing

This document explains how SprigConfig is packaged, versioned, and published to the
GitLab Package Registry, TestPyPI, and the public PyPI index using GitLab CI pipelines.

GitHub Actions is being adopted in phases. The workflow at `.github/workflows/release-checks.yml`
mirrors build and dry-run artifact validation, and `.github/workflows/manual-publish.yml` now adds
manual GitHub-side publishing for TestPyPI and PyPI during the cutover period.

---

# 📦 Packaging Overview

SprigConfig uses **Poetry 2.3.1** as its build and dependency manager.

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

SprigConfig now has three publishing targets with different authentication models:

## GitLab Package Registry

Publishing to the internal GitLab registry uses Poetry with HTTP basic auth:

```
POETRY_HTTP_BASIC_GITLAB_PYPI_USERNAME="__token__"
POETRY_HTTP_BASIC_GITLAB_PYPI_PASSWORD="${CI_JOB_TOKEN}"
```

These variables are already configured in `.gitlab-ci.yml`.

## Public PyPI

Publishing to `pypi.org` uses Trusted Publishing:

- GitLab issues an OIDC ID token for the publish job
- PyPI exchanges that token for a short-lived API token
- `twine upload` publishes without storing a long-lived PyPI secret in GitLab

The GitLab trusted publisher on PyPI must match:

- Project name: `sprig-config`
- Namespace: `dgw_software`
- Repository: `sprig-config`
- Top-level CI configuration path: `.gitlab-ci.yml`

If you want to publish manually from GitHub Actions during the migration, add a second trusted
publisher entry on PyPI that matches:

- Owner or organization: `derikgw` or the GitHub owner that hosts the mirror
- Repository: `sprig-config`
- Workflow path: `.github/workflows/manual-publish.yml`
- Environment: `pypi-production` (if you enforce environment-scoped publishing)

## TestPyPI

Publishing to `test.pypi.org` also uses Trusted Publishing:

- Branch pipelines request an OIDC ID token with audience `testpypi`
- `twine upload --repository testpypi` publishes to TestPyPI
- The CI job rewrites the version to `<base>.dev<CI_PIPELINE_IID>` before build
  so every branch publish is unique and does not collide with TestPyPI's immutability

If GitHub Actions should also publish to TestPyPI during the cutover, add a matching trusted
publisher entry there for `.github/workflows/manual-publish.yml` and the `testpypi` environment.

---

# 🧭 Registry Configuration in pyproject.toml

```
[[tool.poetry.source]]
name = "gitlab-pypi"
url = "https://gitlab.com/api/v4/projects/72230105/packages/pypi"
priority = "supplemental"
```

Details:

- PyPI.org remains the primary source  
- GitLab registry is supplemental  
- GitLab CI can publish to either registry depending on the manual deploy job

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

### 2️⃣ CI runs one or more validation jobs

- `dry_run_pypi`
  - Ensures tag matches version
  - Builds the package
  - Runs a simulated publish to the GitLab registry
- `dry_run_testpypi`
  - Runs on branch pipelines
  - Rewrites the package version to `<base>.dev<CI_PIPELINE_IID>`
  - Builds the package and validates artifacts with `twine check`
- `dry_run_public_pypi`
  - Ensures tag matches version
  - Builds the package
  - Runs `twine check dist/*` before any public upload

GitHub Actions now mirrors these dry-run checks by:

- building and validating distributions on pull requests and `main`
- validating release tags with `scripts/verify-release-tag.sh`
- offering a manual TestPyPI-style build that rewrites the version to `<base>.dev<run_number>`

### 3️⃣ CI runs one or more deploy jobs (manual approval)

- `deploy_pypi`
  - Performs `poetry publish --no-interaction -r gitlab-pypi`
  - Uploads artifacts to the GitLab Package Registry
- `deploy_testpypi`
  - Runs on branch pipelines
  - Requests a GitLab OIDC token with audience `testpypi`
  - Runs `twine upload --repository testpypi`
  - Uploads uniquely versioned branch artifacts to TestPyPI
- `deploy_public_pypi`
  - Requests a GitLab OIDC token with audience `pypi`
  - Runs `twine upload` with PyPI Trusted Publishing
  - Uploads artifacts to `pypi.org`

GitHub Actions now also offers a manual release path through `.github/workflows/manual-publish.yml`:

- choose `target=testpypi` and `mode=validate|publish` on a branch ref
- choose `target=pypi` and `mode=validate|publish` on a `v*` or `V*` tag ref
- keep GitLab deploy jobs enabled until GitHub publishing has proven itself, then disable the
  GitLab publish jobs to avoid duplicate releases from mirrored tags

This ensures:

- Reproducible publishing  
- No accidental uploads  
- Manual human approval  

During the transition, publishing can be driven manually from either GitLab CI or GitHub Actions.
Avoid enabling both for the same release event unless one side is explicitly left in validation-only mode.

---

# 📥 Consuming SprigConfig from GitLab PyPI

Add this to the consumer project's `pyproject.toml`:

```
[[tool.poetry.source]]
name = "sprigconfig-internal"
url = "https://gitlab.com/api/v4/projects/72230105/packages/pypi"
priority = "supplemental"
```

Then:

```
poetry add sprig-config
```

---

# 🧪 Troubleshooting

### ❌ 401 Unauthorized  
GitLab registry credentials are missing or lack `write_registry`.

### ❌ invalid-publisher / invalid-pending-publisher
The trusted publisher registered on PyPI or TestPyPI does not match the active release system
(GitLab project / `.gitlab-ci.yml`, or GitHub repo / `.github/workflows/manual-publish.yml`).

### ❌ file already exists
The version being uploaded has already been published to TestPyPI or PyPI.
Branch builds avoid this by using a `.dev<CI_PIPELINE_IID>` suffix in CI.

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
- Safe (manual validation before release)
- Published only on valid version tags
- Available from both the GitLab registry and the public PyPI index

This keeps internal distribution and public package distribution aligned without adding a
long-lived PyPI token to GitLab.
