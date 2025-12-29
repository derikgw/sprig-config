#!/usr/bin/env python3
"""
Basic SprigConfig Example

This script demonstrates the simplest usage of SprigConfig:
loading configuration from a YAML file and accessing values.
"""

from sprigconfig import load_config


def main():
    """Load and display configuration values."""

    # Load configuration from ./config/application.yml
    cfg = load_config()

    print("=" * 60)
    print("SprigConfig - Basic Usage Example")
    print("=" * 60)
    print()

    # Access nested configuration using dict syntax
    print("Database Configuration:")
    print(f"  Host: {cfg['database']['host']}")
    print(f"  Port: {cfg['database']['port']}")
    print(f"  Database: {cfg['database']['name']}")
    print(f"  Pool Size: {cfg['database']['pool_size']}")
    print()

    # Access configuration values
    print("Application Settings:")
    print(f"  Name: {cfg['app']['name']}")
    print(f"  Version: {cfg['app']['version']}")
    print(f"  Debug: {cfg['app']['debug']}")
    print(f"  Max Connections: {cfg['app']['max_connections']}")
    print()

    # Using dotted-key access (alternative syntax)
    print("Using dotted-key access:")
    print(f"  database.host = {cfg.get('database.host')}")
    print(f"  app.debug = {cfg.get('app.debug')}")
    print(f"  logging.level = {cfg.get('logging.level')}")
    print()

    # Check if features are enabled
    print("Feature Flags:")
    print(f"  Cache: {'enabled' if cfg['features']['enable_cache'] else 'disabled'}")
    print(f"  Metrics: {'enabled' if cfg['features']['enable_metrics'] else 'disabled'}")
    print(f"  Profiling: {'enabled' if cfg['features']['enable_profiling'] else 'disabled'}")
    print()

    # Access the profile (defaults to 'dev' when not specified)
    print(f"Active Profile: {cfg.get('app.profile')}")
    print()

    print("=" * 60)


if __name__ == "__main__":
    main()
