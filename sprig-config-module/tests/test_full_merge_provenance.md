# tests/test_full_merge_provenance.py — Documentation

This integration test validates **SprigConfig’s full merge provenance** — confirming
that the configuration engine merges all expected files, respects import order,
applies profile overlays correctly, and produces truthful metadata in `_meta`.

---

## Purpose

To ensure that `ConfigLoader` not only merges configurations correctly but that
the resulting `_meta` information (sources, import order, and profile) **accurately
reflects the merge process**.

This is the highest‑level test in the suite: it exercises `ConfigLoader` across
real files and real merge paths, providing end‑to‑end validation of SprigConfig’s
core behavioral contract.

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

| Category | Guarantee | Description |
|-----------|------------|--------------|
| **Meta completeness** | ✅ `_meta.sources` includes every file loaded | Ensures that all base, import, and profile files appear in metadata |
| **Meta correctness** | ✅ Each `_meta` source actually exists on disk | Protects against stale or missing entries |
| **Import order** | ✅ `_meta.import_trace` respects file precedence | Validates deterministic merge order |
| **Overlay behavior** | ✅ Profile overlays override base values | Confirms profile-specific behavior (e.g., `application-dev.yml`) |
| **Additive merges** | ✅ Lists and maps merge correctly | Verifies additive semantics rather than destructive overwrites |
| **Key preservation** | ✅ Base keys persist unless explicitly overridden | Ensures no unexpected data loss |
| **Profile truthfulness** | ✅ `_meta.profile` matches active profile | Confirms provenance metadata integrity |

---

## Test Design

### 1️⃣ Setup

The test uses real files under `tests/config/`, including:

- `application.yml` (base configuration)
- `application-dev.yml` (profile overlay)
- `imports/common.yml` (imported values)

These files contain nested maps, lists, and overlays representative of typical
SprigConfig usage.

### 2️⃣ Execution

```python
loader = ConfigLoader(config_dir="tests/config", profile="dev")
config = loader.load()
meta = config["_meta"]
```

The loader processes all files, recursively following imports and overlays.

### 3️⃣ Assertions

| Step | Purpose |
|------|----------|
| `_meta.sources` contains all expected files | Verifies full provenance |
| `_meta.import_trace` ordering is correct | Ensures deterministic merge sequence |
| Overlays override base keys | Confirms correct profile behavior |
| Additive merges succeed | Ensures list/dict merges behave correctly |
| `_meta.profile` matches `"dev"` | Confirms metadata consistency |

### 4️⃣ Sanity & Integrity Checks

The test also verifies:

- Each file in `_meta.sources` exists on disk
- Nothing essential (like `app` or `metadata`) disappears during merge
- `_meta` fields (`profile`, `sources`, `import_trace`) are all present

---

## Example Success Output

```
✅ Full merge provenance verified successfully.
```

---

## Why This Test Matters

SprigConfig’s merging engine is the **core feature** of the library.
This test proves that:

- Merges are deterministic  
- Imports are traceable  
- Profiles apply predictably  
- Metadata is trustworthy  

It provides the single strongest assurance that SprigConfig behaves consistently
across environments, which is essential for stable CI/CD pipelines and 1.0.0‑level
confidence.

---

## Relationship to Other Tests

| File | Role |
|------|------|
| `test_deep_merge.py` | Verifies low‑level merge semantics |
| `test_import_trace.py` | Verifies import path recording |
| `test_profiles.py` | Verifies profile overlays individually |
| **`test_full_merge_provenance.py`** | Combines all of the above to validate holistic behavior |

---

## Future Enhancements

- Validate `_meta.import_trace` against generated `Config.sources`
- Add diff visualization for import layering (future `--trace` CLI mode)
- Extend test to include `LazySecret` behavior in merged context
- Consider a `ConfigIntegrityReport` helper for automated provenance checks

---

Generated documentation for `tests/test_full_merge_provenance.py`.
