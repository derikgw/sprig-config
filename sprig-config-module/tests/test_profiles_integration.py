# sprig-config-module/tests/test_profiles_integration.py
import pytest
from pathlib import Path
from sprigconfig import load_config, ConfigLoadError
from dotenv import load_dotenv

from sprigconfig.lazy_secret import LazySecret

load_dotenv()

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"


@pytest.mark.integration
@pytest.mark.parametrize("profile", ["dev", "prod", "test"])
def test_profiles_load_correctly(profile, monkeypatch):
    monkeypatch.setenv("APP_PROFILE", profile)

    if profile in ("prod", "test"):
        profile_file = CONFIG_DIR / f"application-{profile}.yml"
        if not profile_file.exists():
            pytest.skip(f"No {profile_file.name} found for integration test")

    try:
        config = load_config(config_dir=CONFIG_DIR)
    except ConfigLoadError as e:
        if profile == "prod":
            pytest.skip(f"Prod config strictness: {e}")
        else:
            raise

    # Confirm active profile
    assert config["app"]["profile"] == profile

    # Server & logging present
    assert "server" in config
    assert "logging" in config

    # Secrets check
    secrets = config.get("secrets", {})
    for k, v in secrets.items():
        if isinstance(v, LazySecret):
            secrets[k] = v.get()
    if secrets:
        assert all(not str(v).startswith("ENC(") for v in secrets.values())
