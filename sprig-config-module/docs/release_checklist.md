# 🧩 SprigConfig — Release Checklist

A repeatable checklist for publishing **SprigConfig** releases  
(from development → tag → CI/CD → package registry).

---

## 🧱 1️⃣  Prep & Verify

- [ ] Ensure all tests pass locally:
  ```bash
  poetry run pytest
  ```
- [ ] Verify coverage and logs:
  ```bash
  poetry run pytest --cov=src --maxfail=1 -q
  ```
- [ ] Confirm version bump in:
  - `pyproject.toml`
  - `src/sprigconfig/__init__.py` (if defined)
- [ ] Update `CHANGELOG.md`
  - Add a new section for the release.
  - Move unreleased changes under `[x.y.z] - YYYY-MM-DD`.

---

## 🧪 2️⃣  Build & Validate Artifacts

- [ ] Clean build directories:
  ```bash
  rm -rf dist/ build/
  ```
- [ ] Build the package:
  ```bash
  poetry build
  ```
- [ ] Verify `.whl` and `.tar.gz` files in `/dist`:
  ```bash
  ls -lh dist/
  ```

---

## 🗾 3️⃣  Commit & Tag

- [ ] Commit the version bump and changelog:
  ```bash
  git add pyproject.toml CHANGELOG.md
  git commit -m "chore(release): prepare v1.x.x"
  ```
- [ ] Create an annotated tag:
  ```bash
  git tag -a v1.x.x -m "🎉 SprigConfig x.x.x — Release notes here"
  ```
- [ ] Push commit + tag:
  ```bash
  git push origin main --tags
  ```

---

## 📦 4️⃣  Verify CI/CD & Publish

- [ ] Check CI validation status:
  - ✅ Lint
  - ✅ Tests
  - ✅ Security Scans
  - ✅ Build artifacts (wheel + sdist)
- [ ] Confirm Trusted Publishing entries exist:
  - TestPyPI publisher for `.github/workflows/manual-publish.yml` + `testpypi` environment
  - PyPI publisher for `.github/workflows/manual-publish.yml` + `pypi-production` environment
- [ ] Run GitHub Actions **Manual Publish** with `target=testpypi`, `mode=publish` on a branch
- [ ] Confirm branch build appears on **TestPyPI**
- [ ] Run GitHub Actions **Manual Publish** with `target=pypi`, `mode=publish` on a `v*`/`V*` tag
- [ ] Confirm package appears on **PyPI**:
  <https://pypi.org/project/sprig-config/>
- [ ] Optional: publish to the GitLab Package Registry if internal mirror distribution is still required
- [ ] Optional emergency fallback: publish manually to PyPI with an API token:
  ```bash
  cd sprig-config-module
  PYPI_API_TOKEN=... ./scripts/upload-to-pypi.sh
  ```

---

## 🚀 5️⃣  Post-Release Tasks

- [ ] Verify installation works:
  ```bash
  pip install sprig-config==x.x.x
  ```
- [ ] Announce release:
  - Update **README.md** “Latest Version” badge if applicable
  - Post tag URL to project log or LinkedIn
- [ ] Create next placeholder in `CHANGELOG.md`:
  ```markdown
  ## [Unreleased]
  - Upcoming features and fixes
  ```

---

### ✅ Summary

| Stage | Purpose | Status |
|--------|----------|---------|
| Prep | Ensure version, changelog, tests are ready | ☑ |
| Build | Generate clean, verifiable artifacts | ☑ |
| Tag | Create annotated version tag | ☑ |
| CI/CD | Confirm GitHub validation/publish runs or the GitLab publish pipeline, and verify the registry upload | ☑ |
| Post | Verify install, update docs, announce release | ☑ |

---

**Stable. Secure. Predictable.**
