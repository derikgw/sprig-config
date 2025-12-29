# SprigConfig Migration Guide

This guide helps you upgrade SprigConfig across versions. SprigConfig follows [Semantic Versioning](https://semver.org/), so:

- **MAJOR** versions (e.g., 1.x → 2.x) may introduce breaking changes
- **MINOR** versions (e.g., 1.1 → 1.2) add features while maintaining backward compatibility
- **PATCH** versions (e.g., 1.2.3 → 1.2.4) contain only bug fixes and are always safe to upgrade

## Quick Version Check

```bash
# Check your current version
python -c "import sprigconfig; print(sprigconfig.__version__)"

# Or via pip
pip show sprigconfig | grep Version
```

## Current Version: 1.2.4

All 1.x releases are backward compatible. You can safely upgrade from any 1.x version to 1.2.4.

---

## Upgrading to 1.2.x (TOML Support)

**From:** 1.0.x, 1.1.x
**To:** 1.2.0+
**Risk:** Low
**Breaking Changes:** None

### What's New

- **TOML configuration format support** (in addition to YAML and JSON)
- **CLI `--format` flag** for explicit format selection
- **Merge order fix** for imports and profile overlays

### Installation

```bash
pip install --upgrade sprigconfig
```

### Migration Steps

#### 1. No Action Required

If you're using YAML or JSON configurations, **no changes are needed**. Your existing configuration will continue to work exactly as before.

#### 2. Optional: Adopt TOML

If you want to use TOML instead of YAML:

**Before (YAML):**
```yaml
# config/application.yml
database:
  host: localhost
  port: 5432
```

**After (TOML):**
```toml
# config/application.toml
[database]
host = "localhost"
port = 5432
```

**Important:** Use **exactly one format** per project. Mixed-format imports are not supported.

#### 3. Review Merge Order Behavior

Version 1.2.0 fixed a merge order bug. If you were relying on imports to override profile values (which was unintended behavior), you may see different results.

**Correct merge order (1.2.0+):**
1. Base config (`application.yml`)
2. Base imports
3. Profile overlay (`application-<profile>.yml`)
4. Profile imports

**Profile overlays now have final say**, which is the intended behavior.

**Action:** Test your configuration merging in a dev environment before deploying to production.

### Testing Your Migration

```bash
# Verify configuration loads correctly
sprigconfig dump --profile dev

# Check merge order
sprigconfig dump --profile prod --show-provenance
```

---

## Upgrading to 1.1.x (JSON Support)

**From:** 1.0.x
**To:** 1.1.0+
**Risk:** Very Low
**Breaking Changes:** None

### What's New

- **JSON configuration format support** (in addition to YAML)
- Format-agnostic configuration loading
- Extension-aware config discovery
- Internal parser abstraction

### Installation

```bash
pip install --upgrade sprigconfig
```

### Migration Steps

#### 1. No Action Required

YAML configurations continue to work without any changes.

#### 2. Optional: Use JSON

If you prefer JSON format:

**Before (YAML):**
```yaml
# config/application.yml
app:
  name: MyApp
  debug: true
```

**After (JSON):**
```json
// config/application.json
{
  "app": {
    "name": "MyApp",
    "debug": true
  }
}
```

#### 3. Environment Variable Changes (Optional)

If you were using undocumented environment variables for format selection, use the new standard:

```bash
# Old (undocumented, may not work)
CONFIG_FORMAT=json

# New (official)
SPRIGCONFIG_FORMAT=json
```

### Testing Your Migration

```bash
# Verify YAML still works
sprigconfig dump --profile dev

# Or try JSON
sprigconfig dump --profile dev --format json
```

---

## Upgrading from Pre-1.0

If you're upgrading from a pre-release or development version, please review the [1.0.0 release notes](../CHANGELOG.md#100--2025-12-02) carefully for breaking changes and migration requirements.

---

## Common Migration Scenarios

### Scenario 1: Simple YAML Configuration

**Question:** I only use basic YAML files. Do I need to change anything?

**Answer:** No. All 1.x versions are fully backward compatible with basic YAML configurations.

### Scenario 2: Using Encrypted Secrets

**Question:** Will my encrypted secrets still work?

**Answer:** Yes. Secret handling is unchanged across all 1.x versions. Your `ENC()` values will continue to work exactly as before.

### Scenario 3: Multiple Environments (Profiles)

**Question:** I use dev, test, and prod profiles. Will they work?

**Answer:** Yes. Profile handling is unchanged, though the merge order fix in 1.2.0 ensures profile overlays correctly override imported values (as intended).

### Scenario 4: Recursive Imports

**Question:** I have complex import chains. Will they break?

**Answer:** No. Import handling is backward compatible. The 1.2.0 merge order fix actually makes imports work more correctly.

---

## Deprecation Policy

SprigConfig follows these deprecation principles:

1. **No surprise removals** - Features are deprecated for at least one MINOR version before removal
2. **Clear warnings** - Deprecated features log warnings when used
3. **Migration path** - Alternatives are provided before deprecation
4. **Semantic versioning** - Breaking changes only occur in MAJOR versions

### Currently Deprecated

**None.** All features in SprigConfig 1.x are actively supported.

---

## Python Version Compatibility

| SprigConfig Version | Python Versions | Notes |
|---------------------|-----------------|-------|
| 1.2.4 (current)     | 3.13+          | Strict requirement |
| 1.2.0 - 1.2.3       | 3.13+          | Strict requirement |
| 1.1.0               | 3.13+          | Strict requirement |
| 1.0.0               | 3.13+          | Strict requirement |

**Note:** SprigConfig requires Python 3.13 or newer. Earlier Python versions are not supported.

---

## Troubleshooting Upgrades

### Issue: Configuration not loading after upgrade

**Symptoms:**
- `ConfigLoadError` exceptions
- Missing configuration values
- Unexpected merge results

**Solutions:**

1. **Verify your SprigConfig version:**
   ```bash
   pip show sprigconfig
   ```

2. **Check configuration file syntax:**
   ```bash
   # For YAML
   python -c "import yaml; yaml.safe_load(open('config/application.yml'))"

   # For JSON
   python -c "import json; json.load(open('config/application.json'))"
   ```

3. **Dump configuration to see what's loaded:**
   ```bash
   sprigconfig dump --profile dev
   ```

4. **Enable debug logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)

   from sprigconfig import load_config
   cfg = load_config()
   ```

### Issue: Merge order changed in 1.2.0

**Symptoms:**
- Profile values are different than expected
- Imports seem to override profile settings

**Solution:**

This is the intended behavior fix. Profile overlays should have final say.

**Before (incorrect, pre-1.2.0):**
```
1. Base config
2. Base imports (could override base)
3. Profile overlay
4. Profile imports (could override profile!) ← Bug
```

**After (correct, 1.2.0+):**
```
1. Base config
2. Base imports
3. Profile overlay (overrides everything above)
4. Profile imports (extends profile)
```

If you were relying on the old behavior, move values from imports to profile overlays.

### Issue: Secrets not decrypting

**Symptoms:**
- `LazySecret` objects not decrypting
- "Invalid token" or decryption errors

**Solutions:**

1. **Verify `APP_SECRET_KEY` is set:**
   ```bash
   echo $APP_SECRET_KEY
   ```

2. **Check key matches the encryption key:**
   Secrets encrypted with key A cannot be decrypted with key B.

3. **Re-encrypt with current key:**
   ```python
   from sprigconfig.lazy_secret import LazySecret

   new_encrypted = LazySecret.encrypt("my-secret", key)
   ```

---

## Getting Help

If you encounter issues during migration:

1. **Check the [CHANGELOG](../CHANGELOG.md)** for version-specific notes
2. **Review the [FAQ](https://dgw-software.gitlab.io/sprig-config/faq/)**
3. **File an issue** on [GitLab](https://gitlab.com/dgw_software/sprig-config/-/issues)

---

## Future Migrations

### Preparing for 2.0.0

SprigConfig 2.0.0 (tentative) may introduce:

- Plugin system with stable contracts
- Enhanced validation
- Advanced debugging features

**What to expect:**
- Breaking changes will be clearly documented
- Migration guide will be provided before release
- Deprecation warnings in 1.x versions
- Extended support for 1.x after 2.0 release

Check the [ROADMAP](../ROADMAP.md) for planned features.

---

## Best Practices for Upgrades

1. **Test in development first** - Never upgrade directly in production
2. **Review release notes** - Read the CHANGELOG before upgrading
3. **Run your test suite** - Ensure all tests pass with the new version
4. **Check configuration dumps** - Verify merged config is correct
5. **Monitor after deployment** - Watch for configuration-related errors
6. **Have a rollback plan** - Pin versions in requirements.txt

**Example pinning:**
```txt
# Pin to specific version
sprigconfig==1.2.4

# Or allow patch updates only
sprigconfig~=1.2.0
```

---

## Version History Summary

| Version | Release Date | Key Changes | Breaking |
|---------|--------------|-------------|----------|
| 1.2.4   | 2025-12-21   | TOML feature parity | No |
| 1.2.0   | 2025-12-20   | TOML support, merge order fix | No |
| 1.1.0   | 2025-12-15   | JSON support | No |
| 1.0.0   | 2025-12-02   | Initial stable release | N/A |

See [CHANGELOG](../CHANGELOG.md) for complete version history.
