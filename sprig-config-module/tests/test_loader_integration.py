# sprig-config-module/tests/test_loader_integration.py
import pytest
import yaml
from sprigconfig import load_config

@pytest.fixture
def full_config_dir(tmp_path):
    """Creates a realistic config tree for deep merge + import testing."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Base config
    (config_dir / "application.yml").write_text(
        yaml.dump({
            "app": {"name": "testapp"},
            "server": {"port": 8080},
            "features": {"auth": {"enabled": True}, "cache": {"enabled": True}},
            "logging": {"level": "INFO", "format": "%(message)s"},
        })
    )

    # Dev profile (overrides port, adds nested feature)
    (config_dir / "application-dev.yml").write_text(
        yaml.dump({
            "server": {"port": 9090},
            "features": {"auth": {"enabled": True, "mode": "dev-only"}},
            "imports": ["import-extra.yml"],
        })
    )

    # Import file (adds more nested keys)
    (config_dir / "import-extra.yml").write_text(
        yaml.dump({
            "server": {"host": "localhost"},
            "features": {"extra": {"enabled": True}},
        })
    )

    return config_dir


def test_config_profiles_merge(full_config_dir, maybe_dump):
    cfg = load_config(profile="dev", config_dir=full_config_dir)
    maybe_dump(cfg)
    # Base keys remain
    assert "server" in cfg
    assert "features" in cfg
    # Port overridden
    assert cfg["server"]["port"] == 9090
    # Host merged from import
    assert cfg["server"]["host"] == "localhost"
    # Feature merges preserved
    assert cfg["features"]["auth"]["mode"] == "dev-only"
    assert cfg["features"]["extra"]["enabled"] is True


def test_profile_overrides_base_port(full_config_dir):
    cfg = load_config(profile="dev", config_dir=full_config_dir)
    assert cfg["server"]["port"] == 9090
    assert cfg["server"]["host"] == "localhost"


def test_nested_deep_merge_preserves_other_keys(full_config_dir):
    cfg = load_config(profile="dev", config_dir=full_config_dir)
    # Both base and new keys must exist
    assert "auth" in cfg["features"]
    assert "cache" in cfg["features"]
    assert "extra" in cfg["features"]


def test_import_chain_final_values(full_config_dir):
    cfg = load_config(profile="dev", config_dir=full_config_dir)
    # Check final merged values
    assert cfg["server"]["port"] == 9090
    assert cfg["server"]["host"] == "localhost"
    assert cfg["features"]["auth"]["mode"] == "dev-only"
