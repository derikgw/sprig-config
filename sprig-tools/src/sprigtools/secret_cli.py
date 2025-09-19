#!/usr/bin/env python3

# tools/secret_cli.py

# Keygen / Encrypt / Decrypt for sprig-config secrets.

# - Default scheme: fernet  -> outputs ENC(...)

# - Optional scheme: aesgcm -> outputs enc:v1:aesgcm:<nonce>:<ciphertext>


from __future__ import annotations

import argparse

import base64

import getpass

import os

import sys

from typing import Optional

AES_PREFIX = "enc:v1:aesgcm:"

AAD = b"sprig:v1"


def _b64u_enc(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


def _b64u_dec(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _read_key_bytes_from_text(text: str) -> bytes:
    kb = _b64u_dec(text)

    if len(kb) != 32:
        raise ValueError("Provided key must decode to exactly 32 bytes (base64url).")

    return kb


def _read_key_bytes(_scheme: str, key_override: Optional[str]) -> bytes:
    raw = key_override or os.environ.get("APP_SECRET_KEY")

    if not raw:
        raise ValueError("APP_SECRET_KEY not set. Pass --key or export APP_SECRET_KEY.")

    return _read_key_bytes_from_text(raw)


def _keygen_text(scheme: str) -> str:
    if scheme == "fernet":

        from cryptography.fernet import Fernet

        return Fernet.generate_key().decode()

    else:

        return _b64u_enc(os.urandom(32))


def _encrypt_bytes(plaintext: bytes, scheme: str, key_bytes: bytes) -> str:
    if scheme == "fernet":
        from cryptography.fernet import Fernet
        # Fernet expects padded urlsafe base64 text
        key_text = base64.urlsafe_b64encode(key_bytes).decode("ascii")  # <-- padded
        token = Fernet(key_text).encrypt(plaintext).decode("ascii")
        return f"ENC({token})"
    else:

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        nonce = os.urandom(12)

        ct = AESGCM(key_bytes).encrypt(nonce, plaintext, AAD)

        return f"{AES_PREFIX}{_b64u_enc(nonce)}:{_b64u_enc(ct)}"


def _decrypt_bytes(token: str, scheme: str, key_bytes: bytes) -> bytes:
    if scheme == "fernet":
        from cryptography.fernet import Fernet
        key_text = base64.urlsafe_b64encode(key_bytes).decode("ascii")  # <-- padded
        inner = token[4:-1] if token.startswith("ENC(") and token.endswith(")") else token
        return Fernet(key_text).decrypt(inner.encode("ascii"))
    else:

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        if not token.startswith(AES_PREFIX):
            raise ValueError("Expected enc:v1:aesgcm token.")

        try:

            nonce_b64u, ct_b64u = token[len(AES_PREFIX):].split(":", 1)

        except ValueError as e:

            raise ValueError("Malformed AES-GCM token.") from e

        nonce = _b64u_dec(nonce_b64u)

        ct = _b64u_dec(ct_b64u)

        return AESGCM(key_bytes).decrypt(nonce, ct, AAD)


def _read_plaintext(args) -> bytes:
    if getattr(args, "stdin", False):
        return sys.stdin.buffer.read()

    if getattr(args, "text", None) is not None:
        return args.text.encode("utf-8")

    if getattr(args, "prompt", False):
        return getpass.getpass("Secret: ").encode("utf-8")

    # default interactive (echo on)

    return input("Text to encrypt: ").encode("utf-8")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="secret-cli", description="Keygen/encrypt/decrypt for sprig-config.")

    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp):
        sp.add_argument("--scheme", choices=["fernet", "aesgcm"], default="fernet",

                        help="Encryption scheme. Default: fernet (ENC(...))")

        sp.add_argument("--key", help="Base64url APP_SECRET_KEY (overrides env).")

    # keygen

    sp_keygen = sub.add_parser("keygen", help="Generate an APP_SECRET_KEY")

    add_common(sp_keygen)

    # encrypt

    sp_enc = sub.add_parser("encrypt", help="Encrypt a string, optionally generating a fresh key.")

    add_common(sp_enc)

    sp_enc.add_argument("--genkey", action="store_true",

                        help="Generate a fresh key for this encryption (prints APP_SECRET_KEY used).")

    io_group = sp_enc.add_mutually_exclusive_group(required=False)

    io_group.add_argument("--text", help="Plaintext to encrypt.")

    io_group.add_argument("--stdin", action="store_true", help="Read plaintext from stdin (binary-safe).")

    sp_enc.add_argument("--prompt", action="store_true",

                        help="Prompt for secret if --text/--stdin not provided.")

    sp_enc.add_argument("--label", help="Optional label to echo before the token (e.g., 'password').")

    # decrypt

    sp_dec = sub.add_parser("decrypt", help="Decrypt a token to plaintext.")

    add_common(sp_dec)

    sp_dec.add_argument("--token", help="Token to decrypt (reads from stdin if omitted).")

    sp_dec.add_argument("--as-bytes", dest="as_bytes", action="store_true",

                        help="Write raw bytes to stdout (default decodes as UTF-8).")

    return p


def cmd_keygen(args) -> int:
    print(f"APP_SECRET_KEY={_keygen_text(args.scheme)}")

    return 0


def cmd_encrypt(args) -> int:
    if args.genkey:

        key_text = _keygen_text(args.scheme)

        key_bytes = _read_key_bytes_from_text(key_text)

        print(f"APP_SECRET_KEY={key_text}")

    else:

        try:

            key_bytes = _read_key_bytes(args.scheme, args.key)

        except Exception as e:

            print(f"Key error: {e}", file=sys.stderr)

            return 2

    pt = _read_plaintext(args)

    try:

        token = _encrypt_bytes(pt, args.scheme, key_bytes)

    except Exception as e:

        print(f"Encrypt error: {e}", file=sys.stderr)

        return 1

    if args.label:

        print(f"{args.label}: {token}")

    else:

        print(token)

    return 0


def cmd_decrypt(args) -> int:
    token = args.token or sys.stdin.read().strip()

    try:

        key_bytes = _read_key_bytes(args.scheme, args.key)

    except Exception as e:

        print(f"Key error: {e}", file=sys.stderr)

        return 2

    try:

        pt = _decrypt_bytes(token, args.scheme, key_bytes)

    except Exception as e:

        print(f"Decrypt error: {e}", file=sys.stderr)

        return 1

    if args.as_bytes:

        sys.stdout.buffer.write(pt)

    else:

        try:

            print(pt.decode("utf-8"))

        except UnicodeDecodeError:

            print(repr(pt))

    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()

    args = parser.parse_args(argv)

    if args.cmd == "keygen":
        return cmd_keygen(args)

    if args.cmd == "encrypt":
        return cmd_encrypt(args)

    if args.cmd == "decrypt":
        return cmd_decrypt(args)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
