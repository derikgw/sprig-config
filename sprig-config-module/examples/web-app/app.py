#!/usr/bin/env python3
"""
Flask Web Application with SprigConfig Integration

This example demonstrates how to integrate SprigConfig with Flask
for profile-based configuration management.
"""

import sys
import logging
from flask import Flask, jsonify, request
from sprigconfig import load_config


def create_app():
    """Create and configure the Flask application."""

    # Load configuration based on APP_PROFILE environment variable
    # Defaults to 'dev' if not set
    try:
        cfg = load_config()
        profile = cfg.get('app.profile', 'unknown')
        print(f"Loading configuration for profile: {profile}")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    # Create Flask application
    app = Flask(__name__)

    # Configure Flask from SprigConfig
    app.config['DEBUG'] = cfg.get('app.debug', False)
    app.config['SECRET_KEY'] = cfg.get('app.secret_key', 'dev-secret-key')

    # Setup logging
    log_level = getattr(logging, cfg.get('logging.level', 'INFO'))
    logging.basicConfig(
        level=log_level,
        format=cfg.get('logging.format'),
        handlers=[
            logging.FileHandler(cfg.get('logging.file', 'app.log')),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

    # Log startup information
    logger.info(f"Starting {cfg['app']['name']} v{cfg['app']['version']}")
    logger.info(f"Profile: {profile}")
    logger.info(f"Debug mode: {app.config['DEBUG']}")

    # Routes
    @app.route('/')
    def index():
        """Home endpoint."""
        return jsonify({
            'app': cfg['app']['name'],
            'version': cfg['app']['version'],
            'profile': profile,
            'status': 'running'
        })

    @app.route('/health')
    def health():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'profile': profile
        })

    @app.route('/config')
    def show_config():
        """Display non-sensitive configuration (for debugging)."""
        if not app.config['DEBUG']:
            return jsonify({'error': 'Config endpoint only available in debug mode'}), 403

        # Return safe config values (no secrets)
        return jsonify({
            'app': {
                'name': cfg['app']['name'],
                'version': cfg['app']['version'],
                'debug': cfg['app']['debug'],
                'host': cfg['app']['host'],
                'port': cfg['app']['port'],
            },
            'database': {
                'host': cfg['database']['host'],
                'port': cfg['database']['port'],
                'name': cfg['database']['name'],
                'pool_size': cfg['database']['pool_size'],
            },
            'features': cfg['features'],
            'security': {
                'cors_enabled': cfg['security']['cors_enabled'],
                'rate_limit_enabled': cfg['security']['rate_limit_enabled'],
            }
        })

    @app.route('/features')
    def features():
        """Show enabled features."""
        enabled_features = {
            name: enabled
            for name, enabled in cfg['features'].items()
        }
        return jsonify(enabled_features)

    # Setup CORS if enabled
    if cfg.get('security.cors_enabled'):
        from flask_cors import CORS
        cors_origins = cfg.get('security.cors_origins', [])
        CORS(app, origins=cors_origins)
        logger.info(f"CORS enabled for origins: {cors_origins}")

    return app


def main():
    """Run the Flask application."""
    # Load config to get host and port
    cfg = load_config()

    host = cfg.get('app.host', 'localhost')
    port = cfg.get('app.port', 5000)
    debug = cfg.get('app.debug', False)

    print()
    print("=" * 70)
    print(f"Starting {cfg['app']['name']} v{cfg['app']['version']}")
    print(f"Profile: {cfg.get('app.profile')}")
    print(f"Server: http://{host}:{port}")
    print("=" * 70)
    print()
    print("Available endpoints:")
    print(f"  GET  /           - Home")
    print(f"  GET  /health     - Health check")
    print(f"  GET  /config     - Configuration (debug mode only)")
    print(f"  GET  /features   - Feature flags")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()

    # Create and run app
    app = create_app()
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
