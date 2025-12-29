# SprigConfig Examples

This directory contains practical examples demonstrating common SprigConfig usage patterns.

## Examples

### 1. Basic Usage (`basic/`)
Simple configuration loading with YAML files.

**Learn:** Basic config file structure and loading

### 2. Profile-Based Configuration (`profiles/`)
Using profiles (dev, test, prod) to override configuration values.

**Learn:** Profile overlays, runtime profile selection

### 3. Secrets Management (`secrets/`)
Secure handling of sensitive data using encrypted secrets.

**Learn:** ENC() format, LazySecret, key management

### 4. Imports (`imports/`)
Organizing configuration across multiple files with recursive imports.

**Learn:** Import syntax, merge behavior, cycle detection

### 5. Environment Variables (`environment-vars/`)
Dynamic configuration using environment variable expansion.

**Learn:** ${VAR} syntax, defaults, .env files

### 6. Web Application (`web-app/`)
Integrating SprigConfig with Flask/FastAPI web frameworks.

**Learn:** Framework integration, configuration singleton, production patterns

### 7. CLI Application (`cli-app/`)
Building command-line tools with configurable behavior.

**Learn:** CLI integration, argument overrides, configuration inspection

## Running the Examples

Each example directory contains:
- `README.md` - Detailed explanation and instructions
- Configuration files (YAML/JSON/TOML)
- Python scripts demonstrating usage
- `.env.example` - Environment variable templates (where applicable)

To run an example:

```bash
cd examples/<example-name>
# Install SprigConfig if not already installed
pip install sprigconfig
# Follow instructions in the example's README.md
python example.py
```

## Requirements

- Python 3.13+
- SprigConfig 1.2.4+

## Learning Path

If you're new to SprigConfig, we recommend following the examples in order:

1. Start with **Basic Usage** to understand core concepts
2. Move to **Profiles** to learn environment-specific configuration
3. Explore **Imports** for organizing larger configurations
4. Try **Environment Variables** for dynamic values
5. Study **Secrets** for handling sensitive data
6. Check **Web Application** or **CLI Application** based on your use case

## Additional Resources

- [Official Documentation](https://dgw-software.gitlab.io/sprig-config/)
- [GitHub Repository](https://gitlab.com/dgw_software/sprig-config)
- [PyPI Package](https://pypi.org/project/sprigconfig/)
