# Profile-Based Configuration Example

This example demonstrates how to use SprigConfig profiles to manage environment-specific configuration (development, testing, production).

## Files

- `config/application.yml` - Base configuration (shared across all environments)
- `config/application-dev.yml` - Development overrides
- `config/application-test.yml` - Testing overrides
- `config/application-prod.yml` - Production overrides
- `example.py` - Python script demonstrating profile usage

## What You'll Learn

- How profiles override base configuration
- Runtime profile selection
- Deep merge behavior with profile overlays
- Environment-specific settings
- Production safeguards

## Running the Example

```bash
# Run with development profile (default)
python example.py

# Run with test profile
python example.py --profile test

# Run with production profile
python example.py --profile prod
```

## Expected Behavior

### Development Profile
- Debug logging enabled
- Local database connection
- Permissive CORS settings
- Development API endpoints

### Test Profile
- Warning-level logging
- Test database connection
- Automated testing settings
- Mock external services

### Production Profile
- Error-level logging
- Production database with SSL
- Strict security settings
- Real external services

## Key Concepts

### Profile Overlay Pattern

SprigConfig merges configuration in this order:

1. `application.yml` (base configuration)
2. `application-<profile>.yml` (profile-specific overrides)

Values in the profile file **override** corresponding values in the base file using deep merge semantics.

### Runtime Profile Selection

Profiles are determined at runtime (never from config files):

```python
# Explicit profile
cfg = load_config(profile="prod")

# From environment variable
# APP_PROFILE=test
cfg = load_config()

# From pytest context
# Automatically uses "test" when running tests
```

### Best Practices

- **Base file**: Put shared settings in `application.yml`
- **Profile files**: Only include environment-specific overrides
- **Secrets**: Never commit production secrets (use environment variables or encrypted values)
- **Validation**: Production profile requires `application-prod.yml` to exist

## Next Steps

- Try the **secrets** example to learn about secure configuration
- Explore the **imports** example for organizing complex configurations
