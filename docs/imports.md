---
layout: default
title: Imports
---

# Imports

SprigConfig supports recursive configuration imports, allowing you to modularize large configurations into manageable, reusable pieces.

---

## Basic Imports

Use the `imports:` directive to include other configuration files:

```yaml
# application.yml
server:
  port: 8080

imports:
  - database.yml
  - logging.yml
  - features.yml
```

Each imported file is merged into the configuration at the point where the import appears.

---

## Import Resolution

### File paths

Import paths are relative to the configuration directory:

```
config/
├── application.yml
├── database.yml
├── logging.yml
└── features/
    ├── auth.yml
    └── caching.yml
```

```yaml
# application.yml
imports:
  - database.yml
  - logging.yml
  - features/auth.yml
  - features/caching.yml
```

### Extension handling

Import paths can omit the file extension. SprigConfig automatically appends the active format's extension:

```yaml
# With yml format active
imports:
  - database     # Resolves to database.yml
  - logging      # Resolves to logging.yml
```

If you specify an extension, it must match the active format:

```yaml
imports:
  - database.yml  # OK with yml format
  - database.json # Error if yml format is active
```

### Subdirectories

Organize related configuration in subdirectories:

```yaml
imports:
  - common/defaults
  - security/policies
  - integrations/aws
```

---

## Import Order

Files are processed in the order they appear in the `imports:` list:

```yaml
imports:
  - a.yml    # Loaded first
  - b.yml    # Merged on top of a.yml
  - c.yml    # Merged on top of result
```

Later imports can override values from earlier imports.

### Recursive imports

Imported files can themselves have imports:

```yaml
# application.yml
imports:
  - database.yml

# database.yml
database:
  driver: postgresql
imports:
  - database-pools.yml

# database-pools.yml
database:
  pool_size: 10
```

SprigConfig processes these depth-first:
1. Load `database.yml`
2. Recursively load `database-pools.yml` and merge
3. Merge result into `application.yml`

---

## Positional Imports

Imports can appear at any level in the configuration tree, not just at the root:

```yaml
# application.yml
server:
  port: 8080
  imports:
    - server-defaults.yml

database:
  imports:
    - database-defaults.yml
```

### How positional imports work

When imports appear under a key, the imported content merges at that level:

```yaml
# server-defaults.yml (imported under server:)
host: localhost
timeout: 30
ssl: false

# Result
server:
  port: 8080
  host: localhost
  timeout: 30
  ssl: false
```

This is different from root-level imports where content merges at the root.

### Nested example

```yaml
# application.yml
app:
  features:
    imports:
      - feature-flags.yml

# feature-flags.yml
new_ui: true
beta_api: false
dark_mode: true

# Result
app:
  features:
    new_ui: true
    beta_api: false
    dark_mode: true
```

---

## Circular Import Detection

SprigConfig detects and prevents circular imports:

```yaml
# a.yml
imports:
  - b.yml

# b.yml
imports:
  - a.yml  # Creates a cycle!
```

This raises `ConfigLoadError` with a clear message about the cycle.

### Cycle detection is path-based

The same file can be imported from different paths as long as no cycle forms:

```yaml
# application.yml
imports:
  - shared.yml

# application-dev.yml
imports:
  - shared.yml  # OK - not a cycle

# This is fine because they're parallel imports, not circular
```

---

## Security Restrictions

### Path traversal prevention

Imports cannot escape the configuration directory:

```yaml
imports:
  - ../secrets.yml           # Blocked
  - /etc/passwd              # Blocked
  - ../../other-project.yml  # Blocked
```

SprigConfig raises `ConfigLoadError` for any path traversal attempts.

### Absolute paths

Absolute paths are not allowed:

```yaml
imports:
  - /opt/config/shared.yml  # Blocked
```

All imports must be relative to the configuration directory.

---

## Import Trace

Every loaded configuration includes an import trace in its metadata:

```python
cfg = load_config(profile="dev")

trace = cfg["sprigconfig._meta.import_trace"]
for entry in trace:
    print(f"File: {entry['file']}")
    print(f"Depth: {entry['depth']}")
    print(f"Order: {entry['order']}")
```

The trace shows:
- Which files were imported
- The depth in the import tree
- The order they were processed

This helps debug complex import hierarchies.

---

## Common Patterns

### Shared defaults

```yaml
# config/common/defaults.yml
logging:
  format: "%(levelname)s - %(message)s"
  handlers:
    - console
    - file

# config/application.yml
imports:
  - common/defaults.yml

logging:
  level: INFO
```

### Environment-specific overrides

```yaml
# config/application.yml
imports:
  - common/base.yml

# config/application-prod.yml
imports:
  - environments/production.yml
```

### Feature modules

```yaml
# config/application.yml
imports:
  - features/auth.yml
  - features/caching.yml
  - features/notifications.yml
```

### Layered security

```yaml
# config/application.yml
imports:
  - security/defaults.yml

# config/application-prod.yml
imports:
  - security/hardened.yml
```

---

## Import Behavior with Profiles

Both base and profile files can have imports:

```yaml
# application.yml
imports:
  - common/base.yml

# application-prod.yml
imports:
  - production/settings.yml
```

Processing order:
1. `application.yml`
2. Imports from `application.yml`
3. `application-<profile>.yml`
4. Imports from `application-<profile>.yml`

Profile imports are processed last, giving them final override priority.

---

## Best Practices

### Keep imports organized

```
config/
├── application.yml
├── application-dev.yml
├── application-prod.yml
├── common/
│   ├── database.yml
│   └── logging.yml
├── features/
│   ├── auth.yml
│   └── caching.yml
└── environments/
    ├── development.yml
    └── production.yml
```

### Avoid deep import chains

While SprigConfig supports deep recursion, deeply nested imports are hard to debug:

```yaml
# Harder to follow
a.yml → b.yml → c.yml → d.yml → e.yml

# Easier to follow
application.yml
├── common.yml
├── features.yml
└── environment.yml
```

### Use positional imports for related config

```yaml
# Good: related config together
database:
  imports:
    - database/connection.yml
    - database/pools.yml

# Less clear: scattered at root
imports:
  - database-connection.yml
  - database-pools.yml
  - unrelated-stuff.yml
```

### Document your import structure

Add comments explaining the import hierarchy:

```yaml
# Base configuration with common defaults
# See: common/README.md for import structure
imports:
  - common/logging.yml     # Logging defaults
  - common/security.yml    # Security policies
  - features/index.yml     # Feature configuration
```

---

[← Back to Documentation](index.md)
