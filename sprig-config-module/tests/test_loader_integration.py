# sprig-config-module/tests/test_loader_integration.py
import os
import pytest
import json
from pathlib import Path
# from backend.bootstrap.config.config_loader import load_config
from sprigconfig import load_config


@pytest.mark.integration
def test_config_profiles_merge():
    config = load_config()

    # Confirm what profile is active
    print(f"\nActive profile: {config['app']['profile']}")

    assert config["app"]["profile"] == "dev"  # or whatever is expected
    assert "server" in config
    assert "logging" in config


@pytest.mark.integration
def test_profile_overrides_base_port():
    config = load_config()
    assert config["server"]["port"] != 9090  # dev overrides base
    assert config["server"]["port"] != 8080  # dev overrides base
    assert config["logging"]["level"] == "INFO"  # untouched keys preserved


@pytest.mark.integration
def test_nested_deep_merge_preserves_other_keys():
    config = load_config()
    assert config["features"]["auth"]["enabled"] is True
    assert config["features"]["auth"]["methods"] == ["basic", "oauth", "booty_twap"]
    assert config["features"]["cache"]["ttl"] == 300

@pytest.mark.integration
def test_import_chain_final_values():
    config = load_config()

    # Server port should be from override.yml
    assert config["server"]["port"] == 9999

    # Auth methods should include booty_twap from override.yml
    assert config["features"]["auth"]["methods"] == ["basic", "oauth", "booty_twap"]

    # Auth enabled flag should survive from base
    assert config["features"]["auth"]["enabled"] is True

    # Cache should survive from base
    assert config["features"]["cache"]["ttl"] == 300

    # Logging level should still be INFO from base
    assert config["logging"]["level"] == "INFO"

