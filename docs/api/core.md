# Core API

The core API loads configuration and exposes it as a read-oriented mapping.

## `load_config()`

```python
from pathlib import Path
from sprigconfig import load_config

cfg = load_config(profile="prod", config_dir=Path("config"))
```

`profile` is required. `config_dir` may be omitted only when
`APP_CONFIG_DIR` is set. The optional `schema` argument accepts a dataclass
type; see [Schema Validation](../schema-validation.md).

::: sprigconfig.load_config

## `ConfigLoader`

Use the loader directly to select a file format:

```python
from pathlib import Path
from sprigconfig import ConfigLoader

cfg = ConfigLoader(
    config_dir=Path("config"),
    profile="prod",
    config_format="json",
).load()
```

| Parameter | Required | Meaning |
| --- | --- | --- |
| `config_dir` | Yes, unless passed as `None` with `APP_CONFIG_DIR` set | Configuration directory |
| `profile` | Yes | Runtime overlay name |
| `config_format` | No | `yaml`/`yml`, `json`, or `toml`; defaults to `SPRIGCONFIG_FORMAT`, then YAML |
| `schema` | No | Dataclass type for opt-in validation |

::: sprigconfig.ConfigLoader
    options:
      members:
        - __init__
        - load

## `Config`

`Config` implements `collections.abc.Mapping` and supports literal and dotted
key lookup:

```python
port = cfg["database.port"]
port = cfg["database"]["port"]
timeout = cfg.get("database.timeout", 30)

if "database.port" in cfg:
    print(port)

plain = cfg.to_dict()  # LazySecret values are redacted
yaml_text = cfg.dump()
```

Nested mappings are returned as `Config` objects. Lists remain lists, with
nested mappings wrapped when the configuration is constructed.

`Config.dump()` produces a YAML snapshot of the fully assembled configuration,
which is useful for debugging recursive imports, profile overlays, and
provenance. Secrets are redacted by default, and `sprigconfig_first=True` puts
merge metadata at the top. The CLI supports YAML or JSON output when a JSON
snapshot is needed.

::: sprigconfig.Config
    options:
      members:
        - get
        - __getitem__
        - __contains__
        - to_dict
        - dump

## Loading sequence

1. Resolve YAML/JSON/TOML root files for the requested format.
2. Expand environment placeholders before parsing each file.
3. Resolve recursive imports.
4. Merge the base layer with the optional profile overlay.
5. Run schema validation when `schema=` was supplied.
6. Inject the runtime profile and provenance metadata.
7. Wrap `ENC(...)` strings as `LazySecret` objects.

All files participating in one load use the selected format.
