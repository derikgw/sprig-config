#!/usr/bin/env python3
"""
Secrets Management Example

This script demonstrates how SprigConfig handles encrypted secrets
using the ENC() format and LazySecret objects.
"""

import os
import sys
from sprigconfig import load_config
from sprigconfig.lazy_secret import LazySecret


def generate_example_key():
    """Generate and display an example encryption key."""
    from cryptography.fernet import Fernet

    key = Fernet.generate_key().decode()
    print("=" * 70)
    print("Example Encryption Key Generated")
    print("=" * 70)
    print()
    print("Add this to your environment:")
    print(f"  export APP_SECRET_KEY=\"{key}\"")
    print()
    print("Or copy .env.example to .env and update APP_SECRET_KEY")
    print("=" * 70)
    print()


def encrypt_example_secrets():
    """Encrypt example secret values and show how to use them in config."""
    key = os.environ.get("APP_SECRET_KEY")

    if not key:
        print("Error: APP_SECRET_KEY environment variable not set")
        print()
        generate_example_key()
        return False

    print("=" * 70)
    print("Encrypting Example Secrets")
    print("=" * 70)
    print()

    secrets = {
        "database.password": "my-secret-db-password",
        "api.api_key": "sk-1234567890abcdef",
        "email.password": "my-email-password",
    }

    print("Add these to your config files:")
    print()

    for secret_name, secret_value in secrets.items():
        encrypted = LazySecret.encrypt(secret_value, key)
        print(f"{secret_name}: {encrypted}")

    print()
    print("=" * 70)
    print()

    return True


def demonstrate_lazy_evaluation(cfg):
    """Show how LazySecret objects work."""
    print("=" * 70)
    print("LazySecret Behavior")
    print("=" * 70)
    print()

    # Access the secret object (not yet decrypted)
    db_password = cfg["database"]["password"]
    api_key = cfg["api"]["api_key"]

    print("Before decryption:")
    print(f"  Database password type: {type(db_password).__name__}")
    print(f"  Database password repr: {repr(db_password)}")
    print(f"  API key type: {type(api_key).__name__}")
    print()

    # Note: In a real application, you would decrypt these only when needed
    # For this example, we'll show what happens, but this would fail without
    # the correct encryption key
    print("Attempting to decrypt (this will fail with example encrypted values):")
    try:
        actual_password = db_password.get()
        print(f"  Database password (decrypted): {actual_password}")
    except Exception as e:
        print(f"  Database password: Could not decrypt (expected with example data)")
        print(f"    Error: {type(e).__name__}")

    print()


def demonstrate_redaction(cfg):
    """Show how secrets are redacted in config dumps."""
    print("=" * 70)
    print("Secret Redaction in Config Dumps")
    print("=" * 70)
    print()

    print("Config dump (secrets automatically redacted):")
    print()

    # Show database config with redacted password
    print("database:")
    print(f"  host: {cfg['database']['host']}")
    print(f"  port: {cfg['database']['port']}")
    print(f"  username: {cfg['database']['username']}")
    print(f"  password: {repr(cfg['database']['password'])}")
    print()

    print("api:")
    print(f"  base_url: {cfg['api']['base_url']}")
    print(f"  api_key: {repr(cfg['api']['api_key'])}")
    print()

    print("Note: LazySecret objects are automatically redacted when printed")
    print("      to prevent accidental exposure in logs or error messages.")
    print()


def main():
    """Main demonstration function."""

    # Check if APP_SECRET_KEY is set
    if not os.environ.get("APP_SECRET_KEY"):
        print()
        print("WARNING: APP_SECRET_KEY environment variable not set!")
        print()
        print("To run this example properly:")
        print("1. Generate an encryption key")
        print("2. Set it as APP_SECRET_KEY environment variable")
        print("3. Encrypt your secrets and update the config files")
        print()

        if "--generate-key" in sys.argv:
            generate_example_key()
            return

        if "--encrypt" in sys.argv:
            encrypt_example_secrets()
            return

        print("Run with --generate-key to create a new encryption key")
        print("Run with --encrypt to encrypt example secrets")
        print()

    # Load configuration
    try:
        cfg = load_config()
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return

    print("=" * 70)
    print("SprigConfig - Secrets Management Example")
    print("=" * 70)
    print()

    # Demonstrate lazy evaluation
    demonstrate_lazy_evaluation(cfg)

    # Demonstrate redaction
    demonstrate_redaction(cfg)

    print("=" * 70)
    print("Best Practices:")
    print("=" * 70)
    print()
    print("1. Never commit encryption keys to version control")
    print("2. Use environment variables for production secrets")
    print("3. Decrypt secrets only when needed")
    print("4. Use different keys for different environments")
    print("5. Rotate keys periodically")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
