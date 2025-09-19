#!/usr/bin/env python3
# src/sprigtools/secret_quickdemo.py
# Pure-Python demo: no shell, no piping. Uses secret_cli internals directly.

import os
import getpass

try:
    from .secret_cli import (
        _keygen_text, _read_key_bytes_from_text, _read_key_bytes,
        _encrypt_bytes, _decrypt_bytes,
    )
except ImportError:
    import sys, pathlib
    sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "src"))
    from sprigtools.secret_cli import (
        _keygen_text, _read_key_bytes_from_text, _read_key_bytes,
        _encrypt_bytes, _decrypt_bytes,
    )

def validate_key_text(key_text: str) -> bool:
    try:
        _read_key_bytes_from_text(key_text)
        return True
    except Exception:
        return False

def run(scheme: str = "fernet", genkey: bool = False) -> None:
    # Decide key
    if genkey:
        key_text = _keygen_text(scheme)
        print(f"APP_SECRET_KEY={key_text}")
        key_bytes = _read_key_bytes_from_text(key_text)
        # Note: we can't set the parent shell's env from here; we set our own
        os.environ["APP_SECRET_KEY"] = key_text
        print("Using newly generated key for this run.")
    else:
        env_key = os.environ.get("APP_SECRET_KEY")
        if env_key and validate_key_text(env_key):
            key_text = env_key
            key_bytes = _read_key_bytes(scheme, None)
            print("Using APP_SECRET_KEY from environment.")
        else:
            print("Enter a valid APP_SECRET_KEY to use (input hidden).")
            key_text = getpass.getpass("APP_SECRET_KEY: ")
            if not validate_key_text(key_text):
                raise SystemExit("Invalid key: must be base64url that decodes to 32 bytes.")
            key_bytes = _read_key_bytes_from_text(key_text)
            os.environ["APP_SECRET_KEY"] = key_text  # for this Python process

    # Read plaintext
    secret = getpass.getpass("Secret to encrypt: ").encode("utf-8")

    # Encrypt
    token = _encrypt_bytes(secret, scheme, key_bytes)
    print("Token:")
    print(token)

    # Decrypt to verify
    pt = _decrypt_bytes(token, scheme, key_bytes)
    print("Decrypted:")
    try:
        print(pt.decode("utf-8"))
    except UnicodeDecodeError:
        print(repr(pt))

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Pure-Python secret demo (no shell).")
    ap.add_argument("--scheme", choices=["fernet","aesgcm"], default="fernet")
    ap.add_argument("--genkey", action="store_true", help="Generate a fresh key and use it.")
    args = ap.parse_args()
    run(scheme=args.scheme, genkey=args.genkey)
