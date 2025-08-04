# sprig-config-module/tests/test_loader_integration.py
import os
import pytest
import json
from pathlib import Path
# from backend.bootstrap.config.config_loader import load_config
from sprigconfig import load_config

@pytest.mark.parametrize("profile", ["dev", "prod", "test"])
@pytest.mark.integration
def test_config_profiles_merge(profile):
    os.environ["APP_PROFILE"] = profile
    config = load_config()

    print(f"\n=== {profile.upper()} CONFIG ===")
    print(json.dumps(config, indent=2))

    # Basic sanity: config loads, has core keys
    assert "server" in config
    assert "logging" in config

    # If imports exist, validate them
    imports = config.get("imports", [])
    config_dir = Path(__file__).resolve().parents[4] / "backend" / "config"

    for import_file in imports:
        import_path = config_dir / import_file
        assert import_path.exists(), f"Import file {import_file} not found"
        imported_keys = load_config(profile=profile)["imports"]  # Force re-read to simulate merge
        assert imported_keys is not None
