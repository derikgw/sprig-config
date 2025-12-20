---
layout: default
title: Merge Order
---

# Merge Order

Understanding how SprigConfig merges configuration files is essential for predictable behavior. This guide explains the merge order, deep merge semantics, and how to debug merge issues.

---

## Merge Sequence

SprigConfig loads and merges configuration in this exact order:

```
1. application.<ext>           ← Base configuration
2. Base imports                ← Files from base's imports: directive
3. application-<profile>.<ext> ← Profile overlay
4. Profile imports             ← Files from profile's imports: directive
```

Each step merges into the result of the previous step.

### Visual example

Given these files:

```yaml
# application.yml
server:
  port: 8080
  host: localhost
imports:
  - defaults.yml

# defaults.yml
server:
  timeout: 30

# application-dev.yml
server:
  port: 9090
imports:
  - dev-extras.yml

# dev-extras.yml
server:
  debug: true
```

The merge happens as:

1. Load `application.yml` → `{server: {port: 8080, host: localhost}}`
2. Merge `defaults.yml` → `{server: {port: 8080, host: localhost, timeout: 30}}`
3. Merge `application-dev.yml` → `{server: {port: 9090, host: localhost, timeout: 30}}`
4. Merge `dev-extras.yml` → `{server: {port: 9090, host: localhost, timeout: 30, debug: true}}`

**Key insight:** Profile overlays have the final say. Values in `application-dev.yml` override imported values from `defaults.yml`.

---

## Deep Merge Algorithm

SprigConfig uses a recursive deep merge algorithm with these rules:

### Dictionary + Dictionary

Dictionaries are merged recursively. Keys from both are preserved, with the overlay taking precedence for conflicts.

```yaml
# base
server:
  host: localhost
  port: 8080

# overlay
server:
  port: 9090
  timeout: 30

# result
server:
  host: localhost    # from base
  port: 9090         # from overlay (overrides)
  timeout: 30        # from overlay (new)
```

### List + List

Lists are **completely replaced**, not appended.

```yaml
# base
features:
  - auth
  - logging

# overlay
features:
  - caching

# result
features:
  - caching    # overlay replaces entire list
```

If you want to extend a list, you must repeat all items in the overlay.

### Scalar + Scalar

Scalar values (strings, numbers, booleans) are replaced.

```yaml
# base
port: 8080

# overlay
port: 9090

# result
port: 9090
```

### Missing keys in overlay

Keys present in the base but missing in the overlay are preserved.

```yaml
# base
server:
  host: localhost
  port: 8080

# overlay
server:
  port: 9090
  # host is not mentioned

# result
server:
  host: localhost   # preserved from base
  port: 9090        # from overlay
```

---

## Collision Warnings

SprigConfig warns when overlays might unintentionally lose keys. These warnings help catch configuration mistakes.

### Partial override warning

When an overlay provides only some keys from a nested structure:

```yaml
# base
database:
  host: localhost
  port: 5432
  username: admin
  password: secret

# overlay
database:
  host: db.prod.com
  # port, username, password not mentioned
```

SprigConfig logs a warning indicating that `database` is being partially overridden. The other keys are preserved, but the warning helps catch cases where you might have forgotten to include them.

### Suppressing warnings

If your partial override is intentional, you can suppress warnings:

```yaml
# application.yml
suppress_config_merge_warnings: true
```

Or per-section in your code when using `deep_merge` directly:

```python
from sprigconfig import deep_merge

result = deep_merge(base, overlay, suppress=True)
```

---

## Merge Order With Imports

Imports are processed depth-first as they're encountered. Within an imports list, files are processed in order.

```yaml
# application.yml
imports:
  - a.yml
  - b.yml
```

Processing order:
1. Load `application.yml`
2. Load `a.yml` and merge
3. If `a.yml` has imports, process them recursively
4. Load `b.yml` and merge
5. If `b.yml` has imports, process them recursively

### Positional imports

Imports can appear at any level in the configuration tree:

```yaml
# application.yml
server:
  imports:
    - server-defaults.yml

database:
  imports:
    - database-defaults.yml
```

When imports appear under a key (like `server`), the imported content merges at that level, not at the root.

```yaml
# server-defaults.yml
port: 8080
host: localhost

# Results in:
server:
  port: 8080
  host: localhost
```

---

## Debugging Merge Issues

### Use the CLI

The easiest way to see the final merged result:

```bash
sprigconfig dump --config-dir=config --profile=dev
```

### Check metadata

The merged config includes information about what was loaded:

```python
cfg = load_config(profile="dev")

# See all source files
for source in cfg["sprigconfig._meta.sources"]:
    print(f"Loaded: {source}")

# See the import trace
import_trace = cfg["sprigconfig._meta.import_trace"]
```

### Enable logging

SprigConfig logs merge operations. Enable debug logging to see details:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

You'll see messages like:
- Which files are being loaded
- Override collision warnings
- Import resolution

---

## Common Patterns

### Layered defaults

Use a `defaults.yml` file imported by the base configuration:

```yaml
# application.yml
imports:
  - defaults.yml

# Only specify what's different from defaults
server:
  host: myapp.example.com
```

### Environment-specific databases

Keep database credentials in profile files:

```yaml
# application.yml
database:
  driver: postgresql
  pool_size: 5

# application-prod.yml
database:
  host: ${DB_HOST}
  password: ENC(...)
  pool_size: 20
```

### Feature flags by profile

```yaml
# application.yml
features:
  new_ui: false
  beta_api: false

# application-dev.yml
features:
  new_ui: true
  beta_api: true

# application-prod.yml
features:
  new_ui: true    # Rolled out to production
  beta_api: false # Not yet in production
```

---

## Key Points

1. **Profile overlays win** — They're loaded last and override everything
2. **Lists replace, don't append** — Include all items you want
3. **Deep merge preserves** — Keys not mentioned in overlays are kept
4. **Order is deterministic** — Same inputs always produce same output
5. **Warnings help** — Pay attention to collision warnings

---

[← Back to Documentation](index.md)
