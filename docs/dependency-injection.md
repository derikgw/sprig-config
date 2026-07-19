# Dependency Injection

SprigConfig offers three opt-in binding patterns. Initialize
`ConfigSingleton` before resolving any values.

## Field values

```python
from sprigconfig import ConfigSingleton, ConfigValue

ConfigSingleton.initialize(profile="prod", config_dir="config")


class Service:
    host = ConfigValue("server.host")
    port: int = ConfigValue("server.port")
```

`ConfigValue` resolves lazily, supports defaults and basic type conversion,
and is read-only.

## Configuration sections

```python
from sprigconfig import ConfigurationProperties


@ConfigurationProperties("database")
class DatabaseSettings:
    host: str
    port: int


settings = DatabaseSettings()
```

The decorator binds keys present in the configured section. It is a binding
convenience, not schema validation; use `schema=` when configuration must fail
fast on missing, unknown, or mistyped keys.

## Function parameters

```python
from sprigconfig import ConfigValue, config_inject


@config_inject
def connect(
    host=ConfigValue("database.host"),
    port=ConfigValue("database.port"),
):
    return host, port
```

Explicit call arguments override injected defaults. Missing keys without a
default raise `ConfigLoadError`.

For implementation details, maintainers can consult
`sprig-config-module/docs/configuration-injection.md` in the repository.
