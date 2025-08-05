#!/usr/bin/env python3
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv


def main():
    # Load .env from project root
    load_dotenv()

    key = os.getenv("APP_SECRET_KEY")
    if not key:
        raise SystemExit("❌ APP_SECRET_KEY not found in .env or environment.")

    fernet = Fernet(key.encode() if isinstance(key, str) else key)

    pairs = {
        "username": "testUser",
        "password": "superSecretPass",
        "apiKey": "ABC123XYZ"
    }

    print("🔐 Generated ENC values:")
    for name, value in pairs.items():
        token = fernet.encrypt(value.encode()).decode()
        print(f"{name}: ENC({token})")


if __name__ == "__main__":
    main()
