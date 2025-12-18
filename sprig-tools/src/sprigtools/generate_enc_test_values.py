#!/usr/bin/env python3
from pathlib import Path
import json
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from sprigtools.enc_util import FIXTURE_FILE
import os


def main():
    load_dotenv()

    key = os.getenv("APP_SECRET_KEY")
    if not key:
        raise SystemExit("❌ APP_SECRET_KEY not found in .env or environment.")

    fernet = Fernet(key.encode())

    if not FIXTURE_FILE.exists():
        raise SystemExit(f"❌ Fixture not found: {FIXTURE_FILE}")

    pairs = json.loads(FIXTURE_FILE.read_text())

    print("🔐 Generated ENC values:")
    for name, value in pairs.items():
        token = fernet.encrypt(value.encode()).decode()
        print(f"{name}: ENC({token})")


if __name__ == "__main__":
    main()
