---
layout: default
title: CLI
---

# Command-Line Interface

SprigConfig includes a CLI for inspecting and debugging configuration. This is invaluable for understanding merged configuration, verifying deployments, and troubleshooting issues.

---

## Installation

The CLI is included when you install SprigConfig:

```bash
pip install sprig-config
```

Verify installation:

```bash
sprigconfig --help
```

---

## The `dump` Command

The primary CLI command loads configuration and displays the merged result.

### Basic usage

```bash
sprigconfig dump --config-dir=config --profile=dev
```

This loads configuration from `config/` with the `dev` profile and prints the merged result to stdout.

### Required arguments

| Argument | Description |
|----------|-------------|
| `--config-dir PATH` | Directory containing configuration files |
| `--profile NAME` | Profile to load (dev, test, prod, etc.) |

### Example output

```bash
$ sprigconfig dump --config-dir=config --profile=dev
```

```yaml
app:
  profile: dev
server:
  host: localhost
  port: 9090
database:
  host: localhost
  port: 5432
  password: <LazySecret>
logging:
  level: DEBUG
sprigconfig:
  _meta:
    profile: dev
    sources:
      - /path/to/config/application.yml
      - /path/to/config/application-dev.yml
```

---

## Command Options

### `--format`

Specify the input configuration format:

```bash
# Load YAML files (default)
sprigconfig dump --config-dir=config --profile=dev --format=yml

# Load JSON files
sprigconfig dump --config-dir=config --profile=dev --format=json

# Load TOML files
sprigconfig dump --config-dir=config --profile=dev --format=toml
```

### `--output-format`

Control the output format:

```bash
# Output as YAML (default)
sprigconfig dump --config-dir=config --profile=dev --output-format=yaml

# Output as JSON
sprigconfig dump --config-dir=config --profile=dev --output-format=json
```

### `--output`

Write to a file instead of stdout:

```bash
sprigconfig dump --config-dir=config --profile=prod --output=merged-config.yml
```

### `--secrets`

Reveal decrypted secrets in output:

```bash
# Default: secrets are redacted
$ sprigconfig dump --config-dir=config --profile=prod
database:
  password: <LazySecret>

# With --secrets: plaintext shown (unsafe!)
$ sprigconfig dump --config-dir=config --profile=prod --secrets
database:
  password: actual-plaintext-password
```

**Warning:** Only use `--secrets` in secure environments. Never pipe to logs or shared outputs.

---

## Use Cases

### Verify configuration before deployment

```bash
# Check what production will see
sprigconfig dump --config-dir=config --profile=prod

# Save for review
sprigconfig dump --config-dir=config --profile=prod --output=prod-review.yml
```

### Compare profiles

```bash
# Dump each profile
sprigconfig dump --config-dir=config --profile=dev --output=dev.yml
sprigconfig dump --config-dir=config --profile=prod --output=prod.yml

# Compare
diff dev.yml prod.yml
```

### Debug merge issues

When configuration doesn't look right:

```bash
# See the full merged result
sprigconfig dump --config-dir=config --profile=dev

# Check what files were loaded
sprigconfig dump --config-dir=config --profile=dev | grep -A 20 "_meta"
```

### Validate CI/CD configuration

Add to your CI pipeline:

```yaml
# GitLab CI example
validate-config:
  script:
    - pip install sprig-config
    - sprigconfig dump --config-dir=config --profile=prod
  rules:
    - changes:
        - config/**/*
```

### Generate documentation

Export your configuration structure:

```bash
sprigconfig dump --config-dir=config --profile=dev --output-format=json > docs/config-schema.json
```

---

## Pytest Integration

SprigConfig provides pytest flags for debugging tests:

### `--dump-config`

Print merged configuration for each test:

```bash
pytest --dump-config tests/
```

### `--dump-config-format`

Choose output format:

```bash
pytest --dump-config --dump-config-format=json tests/
```

### `--dump-config-secrets`

Resolve LazySecrets (still redacted by default):

```bash
pytest --dump-config --dump-config-secrets tests/
```

### `--dump-config-no-redact`

Show plaintext secrets (very unsafe):

```bash
pytest --dump-config --dump-config-secrets --dump-config-no-redact tests/
```

### `--debug-dump`

Write merged configuration to a file after tests:

```bash
pytest --debug-dump=test-config-snapshot.yml tests/
```

### `--env-path`

Use a custom `.env` file:

```bash
pytest --env-path=/path/to/.env.test tests/
```

---

## Error Messages

The CLI provides clear error messages:

### Missing configuration directory

```bash
$ sprigconfig dump --config-dir=nonexistent --profile=dev
Error: Configuration directory not found: nonexistent
```

### Missing profile file

```bash
$ sprigconfig dump --config-dir=config --profile=staging
Error: Profile file not found: config/application-staging.yml
```

### Invalid YAML

```bash
$ sprigconfig dump --config-dir=config --profile=dev
Error: Invalid YAML in config/application.yml: ...
```

### Circular import

```bash
$ sprigconfig dump --config-dir=config --profile=dev
Error: Circular import detected: a.yml → b.yml → a.yml
```

---

## Environment Variables

The CLI respects these environment variables:

| Variable | Description |
|----------|-------------|
| `SPRIGCONFIG_FORMAT` | Default config format (yml, json, toml) |
| `APP_SECRET_KEY` | Fernet key for decrypting secrets |

Example:

```bash
export APP_SECRET_KEY="your-fernet-key"
sprigconfig dump --config-dir=config --profile=prod --secrets
```

---

## Scripting Examples

### Check if configuration loads successfully

```bash
#!/bin/bash
if sprigconfig dump --config-dir=config --profile=prod > /dev/null 2>&1; then
    echo "Configuration valid"
    exit 0
else
    echo "Configuration error"
    exit 1
fi
```

### Extract a specific value

```bash
# Using jq with JSON output
PORT=$(sprigconfig dump --config-dir=config --profile=prod --output-format=json | jq -r '.server.port')
echo "Server port: $PORT"
```

### Validate all profiles

```bash
#!/bin/bash
for profile in dev test prod; do
    echo "Checking $profile..."
    if ! sprigconfig dump --config-dir=config --profile=$profile > /dev/null; then
        echo "FAILED: $profile"
        exit 1
    fi
done
echo "All profiles valid"
```

---

## Best Practices

1. **Never use `--secrets` in CI logs** — Secrets would be exposed
2. **Validate configuration in CI** — Catch errors before deployment
3. **Use JSON output for scripting** — Easier to parse programmatically
4. **Review production config before deploy** — Dump and verify
5. **Keep dump outputs out of version control** — They may contain sensitive info

---

[← Back to Documentation](index.md)
