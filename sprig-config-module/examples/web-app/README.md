# Web Application Integration Example

This example demonstrates how to integrate SprigConfig with a Flask web application for profile-based configuration management.

## Files

- `config/application.yml` - Base web app configuration
- `config/application-dev.yml` - Development overrides
- `config/application-prod.yml` - Production overrides
- `app.py` - Flask application with SprigConfig integration
- `requirements.txt` - Python dependencies

## What You'll Learn

- Integrating SprigConfig with Flask
- Using configuration singleton for web apps
- Profile-based deployment (dev vs prod)
- Environment-specific settings
- Configuration dependency injection

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run in development mode:

```bash
python app.py
# or
APP_PROFILE=dev python app.py
```

3. Run in production mode:

```bash
APP_PROFILE=prod python app.py
```

## Expected Behavior

### Development Mode
- Runs on http://localhost:5000
- Debug mode enabled
- Verbose logging
- CORS enabled for local development
- Uses development database

### Production Mode
- Runs on configured host/port
- Debug mode disabled
- Error-level logging only
- Restricted CORS origins
- Uses production database with connection pooling

## Key Concepts

### Configuration Singleton

In web applications, you typically want to load configuration once at startup:

```python
from sprigconfig import load_config

# Load once at application startup
cfg = load_config()

# Access throughout your application
app.config['DATABASE_URL'] = cfg['database']['url']
```

### Profile Selection

Profile is determined by:
1. `APP_PROFILE` environment variable
2. Command line argument
3. Default: 'dev'

```bash
# Development
APP_PROFILE=dev python app.py

# Production
APP_PROFILE=prod gunicorn app:app
```

### Flask Integration Pattern

```python
from flask import Flask
from sprigconfig import load_config

# Load configuration
cfg = load_config()

# Create Flask app
app = Flask(__name__)

# Configure from SprigConfig
app.config['DEBUG'] = cfg.get('app.debug', False)
app.config['DATABASE_URL'] = cfg['database']['url']
```

### Best Practices

1. **Load config early** - Before creating the Flask app
2. **Use config singleton** - Don't reload on every request
3. **Environment variables** - Override config with APP_PROFILE
4. **Secrets management** - Use LazySecret for sensitive values
5. **Validation** - Validate required config on startup

## Running with Gunicorn (Production)

```bash
# Set production profile
export APP_PROFILE=prod

# Run with Gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 app:app
```

## Testing Different Profiles

```bash
# Test development config
curl http://localhost:5000/config

# Check health endpoint
curl http://localhost:5000/health
```

## Common Patterns

### Database Connection

```python
# Get database URL from config
db_url = cfg['database']['url']

# Or build from components
db_url = f"postgresql://{cfg['database']['username']}:{cfg['database']['password'].get()}@{cfg['database']['host']}:{cfg['database']['port']}/{cfg['database']['name']}"
```

### Feature Flags

```python
if cfg.get('features.enable_analytics'):
    initialize_analytics()

if cfg.get('features.enable_caching'):
    setup_cache(cfg['cache']['ttl_seconds'])
```

### CORS Configuration

```python
from flask_cors import CORS

if cfg.get('security.cors_enabled'):
    CORS(app, origins=cfg['security']['cors_origins'])
```

## Next Steps

- Check the **cli-app** example for command-line tool integration
- Review the **secrets** example for handling sensitive configuration
- See the **imports** example for organizing large configurations
