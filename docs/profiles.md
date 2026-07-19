---
title: Profiles
---

# Profiles

Profiles select an optional overlay named `application-<profile>.<ext>`.
SprigConfig always receives the active profile explicitly at runtime; profile
names are not read from configuration files.

## Loading a profile

```python
from pathlib import Path
from sprigconfig import load_config

cfg = load_config(profile="dev", config_dir=Path("config"))
```

If your application selects profiles through an environment variable, resolve
that policy before calling SprigConfig:

```python
import os

profile = os.environ.get("APP_PROFILE", "dev")
cfg = load_config(profile=profile, config_dir="config")
```

`APP_PROFILE` is a useful application convention, but SprigConfig does not read
it automatically.

## Files and merge behavior

For `profile="prod"` in YAML mode, the loader processes:

1. `application.yaml` or `application.yml`;
2. its recursive imports;
3. `application-prod.yaml` or `application-prod.yml`, when present;
4. the overlay's recursive imports.

Later values override earlier values through the standard deep-merge rules.
Profile names are not restricted to `dev`, `test`, and `prod`.

```yaml
# application.yml
server:
  host: localhost
  port: 8080

# application-prod.yml
server:
  host: api.example.com
```

The resulting `server.port` remains `8080`, while `server.host` becomes
`api.example.com`.

## Missing overlays

A profile overlay is optional. If `application-<profile>` does not exist, the
base configuration still loads and the requested profile is injected as
`app.profile`. Enforce a required production overlay in application startup if
that is part of your deployment policy.

## Runtime profile metadata

The selected profile is available in two generated locations:

```python
assert cfg["app.profile"] == "prod"
assert cfg["sprigconfig._meta.profile"] == "prod"
```

A file-provided `app.profile` value is overwritten by the runtime argument.

## Testing profiles

Tests should pass profiles explicitly:

```python
def test_production_configuration(tmp_path):
    cfg = load_config(profile="prod", config_dir=tmp_path)
    assert cfg["app.profile"] == "prod"
```

There is no automatic pytest profile selection in the public loader API.

[← Back to Documentation](index.md)
