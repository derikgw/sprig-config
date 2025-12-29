#!/usr/bin/env python3
"""
Profile-Based Configuration Example

This script demonstrates how SprigConfig handles environment-specific
configuration using profiles (dev, test, prod).
"""

import argparse
from sprigconfig import load_config


def display_config(cfg, profile):
    """Display configuration values for the active profile."""

    print("=" * 70)
    print(f"SprigConfig - Profile Example (Profile: {profile})")
    print("=" * 70)
    print()

    # Application settings
    print("Application:")
    print(f"  Name: {cfg['app']['name']}")
    print(f"  Version: {cfg['app']['version']}")
    print(f"  Host: {cfg['app']['host']}")
    print(f"  Port: {cfg['app']['port']}")
    print()

    # Database settings
    print("Database:")
    print(f"  Host: {cfg['database']['host']}")
    print(f"  Port: {cfg['database']['port']}")
    print(f"  Name: {cfg['database']['name']}")
    print(f"  Pool Size: {cfg['database']['pool_size']}")
    print(f"  SSL Enabled: {cfg['database']['ssl_enabled']}")
    print()

    # Logging settings
    print("Logging:")
    print(f"  Level: {cfg['logging']['level']}")
    print(f"  Format: {cfg['logging']['format']}")
    print()

    # Security settings
    print("Security:")
    print(f"  CORS Enabled: {cfg['security']['cors_enabled']}")
    print(f"  CORS Origins: {', '.join(cfg['security']['cors_origins'])}")
    print(f"  Rate Limiting: {cfg['security']['rate_limit_enabled']}")
    if cfg['security']['rate_limit_enabled']:
        print(f"    {cfg['security']['rate_limit_requests']} requests per "
              f"{cfg['security']['rate_limit_window_seconds']}s")
    print()

    # Features
    print("Features:")
    print(f"  Analytics: {'enabled' if cfg['features']['enable_analytics'] else 'disabled'}")
    print(f"  Email Notifications: {'enabled' if cfg['features']['enable_email_notifications'] else 'disabled'}")
    print(f"  Background Jobs: {'enabled' if cfg['features']['enable_background_jobs'] else 'disabled'}")
    print(f"  Cache TTL: {cfg['features']['cache_ttl_seconds']}s")
    print()

    # External services
    print("External Services:")
    print(f"  API URL: {cfg['external_services']['api_base_url']}")
    print(f"  Timeout: {cfg['external_services']['timeout_seconds']}s")
    print(f"  Retry Attempts: {cfg['external_services']['retry_attempts']}")
    print()

    print("=" * 70)


def main():
    """Load and display configuration for different profiles."""

    parser = argparse.ArgumentParser(description="Profile-based configuration example")
    parser.add_argument(
        "--profile",
        choices=["dev", "test", "prod"],
        default="dev",
        help="Configuration profile to use (default: dev)"
    )
    args = parser.parse_args()

    # Load configuration with the specified profile
    cfg = load_config(profile=args.profile)

    # Display configuration
    display_config(cfg, args.profile)

    # Show how values differ across profiles
    print("\nProfile Comparison Notes:")
    print("-" * 70)
    if args.profile == "dev":
        print("Development profile:")
        print("  - DEBUG logging for detailed output")
        print("  - Rate limiting disabled")
        print("  - Local database and mock services")
        print("  - Permissive CORS for multiple local ports")
    elif args.profile == "test":
        print("Test profile:")
        print("  - WARNING logging to reduce noise")
        print("  - Features disabled for test isolation")
        print("  - Mock external services")
        print("  - Minimal caching and retries")
    elif args.profile == "prod":
        print("Production profile:")
        print("  - ERROR logging only")
        print("  - All security features enabled")
        print("  - Production database with SSL")
        print("  - Real external services with retries")
    print()


if __name__ == "__main__":
    main()
