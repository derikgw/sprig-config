#!/usr/bin/env python3
import os
import click
from cryptography.fernet import Fernet


@click.group()
def cli():
    """SprigConfig Secrets CLI (for developer use only)"""
    pass


@cli.command()
def generate_key():
    """Generate a new Fernet master key."""
    key = Fernet.generate_key().decode()
    click.echo(f"Generated key: {key}")
    click.echo("⚠️ Store this securely (Vault, AWS Secrets Manager, etc.)")


@cli.command()
@click.argument("plaintext")
@click.option("--key", envvar="APP_SECRET_KEY", help="Fernet master key")
def encrypt(plaintext, key):
    """Encrypt a secret into ENC(...) format."""
    if not key:
        click.echo("❌ APP_SECRET_KEY not set. Use --key or export it as an environment variable.")
        raise SystemExit(1)
    fernet = Fernet(key.encode() if isinstance(key, str) else key)
    token = fernet.encrypt(plaintext.encode()).decode()
    click.echo(f"ENC({token})")


@cli.command()
@click.argument("encrypted_value")
@click.option("--key", envvar="APP_SECRET_KEY", help="Fernet master key")
def decrypt(encrypted_value, key):
    """Decrypt an ENC(...) value back to plaintext."""
    if not key:
        click.echo("❌ APP_SECRET_KEY not set. Use --key or export it as an environment variable.")
        raise SystemExit(1)
    fernet = Fernet(key.encode() if isinstance(key, str) else key)
    if not (encrypted_value.startswith("ENC(") and encrypted_value.endswith(")")):
        click.echo(encrypted_value)
        return
    ciphertext = encrypted_value[4:-1].encode()
    plaintext = fernet.decrypt(ciphertext).decode()
    click.echo(plaintext)


if __name__ == "__main__":
    cli()
