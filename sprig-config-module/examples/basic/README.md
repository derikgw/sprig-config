# Basic Usage Example

This example demonstrates the simplest SprigConfig usage pattern: loading configuration from a single YAML file.

## Files

- `config/application.yml` - Main configuration file
- `example.py` - Python script demonstrating config loading

## What You'll Learn

- Basic configuration file structure
- Loading configuration with `load_config()`
- Accessing configuration values using dict-like syntax
- Using dotted-key access for nested values

## Running the Example

```bash
python example.py
```

## Expected Output

```
Database Configuration:
  Host: localhost
  Port: 5432
  Database: myapp_db

Application Settings:
  Debug: True
  Max Connections: 100

Using dotted-key access:
  db.host = localhost
  app.debug = True
```

## Key Concepts

### Configuration File Structure

SprigConfig uses standard YAML syntax with nested dictionaries:

```yaml
database:
  host: localhost
  port: 5432
  name: myapp_db

app:
  debug: true
  max_connections: 100
```

### Loading Configuration

```python
from sprigconfig import load_config

# Load from default location (./config/)
cfg = load_config()

# Access values
db_host = cfg["database"]["host"]
# or using dotted-key syntax
db_host = cfg.get("database.host")
```

## Next Steps

- Try the **profiles** example to learn about environment-specific configuration
- Explore the **imports** example for organizing larger configurations
