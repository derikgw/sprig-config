# Dynamic Instantiation

`instantiate()` constructs an object from a mapping containing a Python import
path in `_target_`.

```yaml
database:
  _target_: myapp.adapters.PostgresAdapter
  host: localhost
  port: 5432
```

```python
from sprigconfig import instantiate, load_config

cfg = load_config(profile="dev", config_dir="config")
adapter = instantiate(cfg["database"])
```

Nested `_target_` mappings are instantiated recursively by default. Use
`_recursive_=False` to leave nested mappings untouched and
`_convert_types_=False` to disable basic annotation-driven scalar conversion.

The target must use a fully qualified `module.ClassName` path. Import errors,
missing targets, missing required constructor parameters, and conversion
failures raise `ConfigLoadError`.

Treat configuration capable of selecting `_target_` values as trusted input;
loading an arbitrary target imports and executes application code.
