# tests/test_full_merge_provenance.py — Documentation

This integration test checks selected merged values and provenance fields for
the repository's `dev` YAML fixture.

---

## Purpose

It is a fixed-fixture integration check, not a general audit of all merge
paths, formats, or metadata combinations.

---

## Test Name

```
test_full_merge_provenance
```

### Location

```
tests/test_full_merge_provenance.py
```

---

## Behavior Verified

| Category | Assertion | Description |
|-----------|------------|--------------|
| **Expected sources** | ✅ `_meta.sources` has exactly four expected paths | Checks the current base, import, and profile fixture files |
| **Meta correctness** | ✅ Each `_meta` source actually exists on disk | Protects against stale or missing entries |
| **Selected trace order** | ✅ Base trace entry precedes profile entry | Checks these entries, not the full merge order |
| **Overlay behavior** | ✅ Profile overlays override base values | Confirms profile-specific behavior (e.g., `application-dev.yml`) |
| **Selected values** | ✅ Expected profile values appear | Checks `app.profile` and `app.debug_mode` |
| **Profile truthfulness** | ✅ `_meta.profile` matches active profile | Confirms provenance metadata integrity |

---

## Test Design

### 1️⃣ Setup

The test uses fixed files under `tests/config/`, including:

- `application.yml` (base configuration)
- `application-dev.yml` (profile overlay)
- `imports/common.yml` (imported values)

The test compares the set of source paths with four expected fixture paths;
duplicate entries in `_meta.sources` would not be detected by that set check.

### 2️⃣ Execution

```python
loader = ConfigLoader(config_dir="tests/config", profile="dev")
config = loader.load()
meta = config["_meta"]
```

The loader processes the imports and profile overlay used by this fixture.

### 3️⃣ Assertions

| Step | Purpose |
|------|----------|
| `_meta.sources` contains the four expected files and no extras | Checks fixture source membership |
| The base trace entry precedes the profile entry | Checks selected trace ordering |
| Overlays override base keys | Confirms correct profile behavior |
| `_meta.profile` matches `"dev"` | Confirms metadata consistency |

### 4️⃣ Sanity & Integrity Checks

The test also verifies:

- Each file in `_meta.sources` exists on disk
- The `app` and `sprigconfig._meta` sections are present
- `_meta` fields (`profile`, `sources`, `import_trace`) are all present

---

## Example Success Output

```
✅ Full merge provenance verified successfully.
```

---

## Why This Test Matters

For this fixture, the test checks that:

- Selected merged values match expectations
- Expected source paths and selected trace entries are present
- The runtime profile metadata matches the chosen fixture profile

It does not establish behavior across other profiles, formats, arbitrary import
graphs, or all possible merge inputs. More focused suites cover some of those
cases independently.

---

## Relationship to Other Tests

| File | Role |
|------|------|
| `test_deep_merge.py` | Verifies low‑level merge semantics |
| `test_import_trace.py` | Verifies import path recording |
| `test_profiles.py` | Verifies profile overlays individually |
| **`test_full_merge_provenance.py`** | Combines all of the above to validate holistic behavior |

---

## Run

From `sprig-config-module/`:

```bash
poetry run pytest tests/test_full_merge_provenance.py
```
