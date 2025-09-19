# sprig-config-module/tests/test_loader_integration.py
import os
from pathlib import Path

import pytest

from sprigconfig import load_config

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"


@pytest.mark.integration
def test_config_profiles_merge(monkeypatch):
    # Loader should inject the profile from env (not from files).
    monkeypatch.setenv("APP_PROFILE", "dev")

    config = load_config(config_dir=CONFIG_DIR)

    # Confirm active profile injected
    assert config["app"]["profile"] == "dev"

    # Basic structure present
    assert "server" in config
    assert "logging" in config


@pytest.mark.integration
def test_profile_overrides_base_port(monkeypatch):
    """
    Expected layering for dev:
      - base (application.yml): server.port = 8080
      - application-dev.yml imports features.yml and override.yml
      - override.yml sets server.port = 9090

    Because imports are applied from the profile file, the final value is from override.yml.
    """
    monkeypatch.setenv("APP_PROFILE", "dev")

    config = load_config(config_dir=CONFIG_DIR)

    # Final port from override.yml
    assert config["server"]["port"] == 9090   # change to 9999 if your dev file sets it last
    assert config["server"]["port"] != 8080   # not the base value


@pytest.mark.integration
def test_nested_deep_merge_preserves_other_keys(monkeypatch):
    """
    We expect features merged from features.yml + override.yml, without losing unrelated keys.
    Assumptions:
      - features.yml sets:
          features.auth.enabled: true
          features.auth.methods: ["password"]
          (optionally) features.cache: true
      - override.yml finalizes:
          features.auth.methods: ["password", "oauth"]
    """
    monkeypatch.setenv("APP_PROFILE", "dev")

    config = load_config(config_dir=CONFIG_DIR)

    # Auth enabled stays true
    assert config["features"]["auth"]["enabled"] is True

    # Methods reflect final override list
    assert config["features"]["auth"]["methods"] == ["password", "oauth"]
    # If your files use different names (e.g. "basic" or add "booty_twap"),
    # change the expected list accordingly.

    # Cache survives (bool or nested). If you store a TTL instead, adjust this assertion.
    cache_val = config["features"]["cache"]
    assert cache_val is True or isinstance(cache_val, dict)


@pytest.mark.integration
def test_import_chain_final_values(monkeypatch):
    """
    Final, concrete expectations after the import chain.
    """
    monkeypatch.setenv("APP_PROFILE", "dev")

    config = load_config(config_dir=CONFIG_DIR)

    # Server port should be from override.yml (see note in test_profile_overrides_base_port)
    assert config["server"]["port"] == 9090    # change if your dev profile sets a different final value

    # Auth methods should reflect the final merged list from override.yml
    assert config["features"]["auth"]["methods"] == ["password", "oauth"]

    # Auth enabled flag should survive from features.yml
    assert config["features"]["auth"]["enabled"] is True

    # Cache should still be present (bool or object)
    cache_val = config["features"]["cache"]
    assert cache_val is True or isinstance(cache_val, dict)

    # Logging level should still be INFO from base
    assert config["logging"]["level"] == "INFO"
