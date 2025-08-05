# tests/test_crypto.py
import os
from pathlib import Path
import pytest
from cryptography.fernet import Fernet
from sprigconfig import load_config, ConfigLoadError
from sprigconfig.lazy_secret import LazySecret
from dotenv import load_dotenv

load_dotenv()


@pytest.mark.integration(reason="Requires APP_SECRET_KEY from .env")
def test_enc_values_are_lazy_secrets(tmp_path):
    """
    Ensure ENC() values load as LazySecret and decrypt only on access.
    """
    key = os.getenv("APP_SECRET_KEY")
    fernet = Fernet(key.encode() if isinstance(key, str) else key)

    enc_username = fernet.encrypt(b"devUser").decode()
    enc_password = fernet.encrypt(b"superSecretPass").decode()

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "application.yml").write_text(f"""
app:
  profile: dev
  secrets:
    username: ENC({enc_username})
    password: ENC({enc_password})
""")

    config = load_config(config_dir=config_dir)

    # Verify they are LazySecret objects, not decrypted yet
    assert isinstance(config["app"]["secrets"]["username"], LazySecret)
    assert isinstance(config["app"]["secrets"]["password"], LazySecret)

    # Accessing them triggers decryption
    assert config["app"]["secrets"]["username"].get() == "devUser"
    assert config["app"]["secrets"]["password"].get() == "superSecretPass"


@pytest.mark.integration(reason="Requires APP_SECRET_KEY from .env")
def test_mixed_plain_and_enc_values(tmp_path):
    """
    Plain values remain plain, ENC() values are LazySecret.
    """
    key = os.getenv("APP_SECRET_KEY")
    fernet = Fernet(key.encode() if isinstance(key, str) else key)
    enc_password = fernet.encrypt(b"plainSecretPass").decode()

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "application.yml").write_text(f"""
app:
  profile: dev
  secrets:
    username: plainUser
    password: ENC({enc_password})
""")

    config = load_config(config_dir=config_dir)

    # Plain value is not LazySecret
    assert config["app"]["secrets"]["username"] == "plainUser"

    # ENC value is LazySecret
    assert isinstance(config["app"]["secrets"]["password"], LazySecret)
    assert config["app"]["secrets"]["password"].get() == "plainSecretPass"


@pytest.mark.integration(reason="Validates real config with profiles and lazy secrets")
def test_real_config_profiles_and_lazy_secrets():
    config_dir = Path(__file__).resolve().parents[1] / "config"

    config = load_config(config_dir=config_dir)

    # Secrets are LazySecret objects
    secrets = config.get("secrets", {})
    assert isinstance(secrets["username"], LazySecret)
    assert isinstance(secrets["password"], LazySecret)
    assert isinstance(secrets["apiKey"], LazySecret)

    # Access returns decrypted values
    assert secrets["username"].get() == "testUser"
    assert secrets["password"].get() == "superSecretPass"
    assert secrets["apiKey"].get() == "ABC123XYZ"
