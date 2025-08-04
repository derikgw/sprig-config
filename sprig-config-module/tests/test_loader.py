# sprig-config-module/tests/test_loader.py
import os
import logging
import tempfile
from pathlib import Path
import pytest
import yaml
import json

# from backend.bootstrap.config.config_loader import load_config, deep_merge, ConfigLoadError
from sprigconfig import load_config, deep_merge, ConfigLoadError


@pytest.fixture
def temp_config_dir(monkeypatch):
    """Create a temp config dir with base + minimal profile files for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)

        # Always create base config
        base_config = {
            "app_name": "job-service-test",
            "logging": {"level": "INFO", "format": "%(message)s"},  # Multiple keys for partial override test
            "suppress_config_merge_warnings": False
        }
        (config_dir / "application.yml").write_text(yaml.dump(base_config))

        # Patch env so loader reads from temp dir
        monkeypatch.setenv("APP_CONFIG_DIR", str(config_dir))

        def maybe_create_profile(profile):
            """Auto-create minimal profile files for prod/test."""
            profile_file = config_dir / f"application-{profile}.yml"
            if not profile_file.exists():
                profile_config = {
                    "server": {"port": 8000},
                    "logging": {"level": "WARN"},
                    "feature": {"dummy_flag": True}
                }
                profile_file.write_text(yaml.dump(profile_config))

        # Wrap monkeypatch to auto-create prod/test configs
        original_setenv = monkeypatch.setenv
        def setenv_with_profile_check(key, value):
            original_setenv(key, value)
            if key == "APP_PROFILE" and value in ("prod", "test"):
                maybe_create_profile(value)
        monkeypatch.setenv = setenv_with_profile_check

        yield config_dir


def test_dev_profile_missing_config_warns_and_continues(caplog, temp_config_dir, monkeypatch):
    caplog.set_level(logging.INFO)
    monkeypatch.setenv("APP_PROFILE", "dev")
    # Intentionally no application-dev.yml
    config = load_config()
    assert config["logging"]["level"] == "INFO"
    assert "continuing with base config" in caplog.text.lower()


def test_prod_profile_missing_config_fails(temp_config_dir, monkeypatch):
    monkeypatch.setenv("APP_PROFILE", "prod")
    # Remove profile file if auto-created by fixture
    prod_file = temp_config_dir / "application-prod.yml"
    if prod_file.exists():
        prod_file.unlink()
    with pytest.raises(ConfigLoadError):
        load_config()


def test_test_profile_missing_config_fails(temp_config_dir, monkeypatch):
    monkeypatch.setenv("APP_PROFILE", "test")
    # Remove profile file if auto-created by fixture
    test_file = temp_config_dir / "application-test.yml"
    if test_file.exists():
        test_file.unlink()
    with pytest.raises(ConfigLoadError):
        load_config()


def test_merge_warns_on_partial_override(temp_config_dir, caplog, monkeypatch):
    caplog.set_level(logging.WARNING)
    monkeypatch.setenv("APP_PROFILE", "dev")

    # Override missing some keys in logging to trigger partial override warning
    override_config = {"logging": {"level": "DEBUG"}}
    (temp_config_dir / "application-dev.yml").write_text(yaml.dump(override_config))

    load_config()
    assert "partially overridden" in caplog.text.lower()


def test_merge_suppresses_warning_when_flag_set(temp_config_dir, caplog, monkeypatch):
    caplog.set_level(logging.WARNING)
    monkeypatch.setenv("APP_PROFILE", "dev")

    override_config = {
        "logging": {"level": "DEBUG"},
        "suppress_config_merge_warnings": True
    }
    (temp_config_dir / "application-dev.yml").write_text(yaml.dump(override_config))

    load_config()
    assert "partially overridden" not in caplog.text.lower()


def test_deep_merge_overrides_and_adds():
    base = {"server": {"port": 8000, "threads": 4}}
    override = {"server": {"threads": 8}, "feature": {"x": True}}
    merged = deep_merge(base, override, suppress_warnings=True)
    assert merged["server"]["threads"] == 8
    assert merged["server"]["port"] == 8000
    assert merged["feature"]["x"] is True


def test_invalid_yaml_raises_clear_error(temp_config_dir, monkeypatch):
    monkeypatch.setenv("APP_PROFILE", "prod")
    (temp_config_dir / "application-prod.yml").write_text("logging: : : : broken")
    with pytest.raises(ConfigLoadError):
        load_config()


def test_prod_debug_logging_blocked_without_flag(temp_config_dir, monkeypatch):
    monkeypatch.setenv("APP_PROFILE", "prod")
    (temp_config_dir / "application-prod.yml").write_text(
        yaml.dump({"logging": {"level": "DEBUG"}})
    )
    with pytest.raises(ConfigLoadError):
        load_config()


def test_prod_debug_logging_allowed_with_flag(temp_config_dir, monkeypatch):
    monkeypatch.setenv("APP_PROFILE", "prod")
    (temp_config_dir / "application-prod.yml").write_text(
        yaml.dump({"logging": {"level": "DEBUG"}, "allow_debug_in_prod": True})
    )
    config = load_config()
    assert config["logging"]["level"] == "DEBUG"


def test_prod_profile_debug_logging_disallowed(temp_config_dir, monkeypatch):
    monkeypatch.setenv("APP_PROFILE", "prod")
    (temp_config_dir / "application-prod.yml").write_text(
        yaml.dump({"logging": {"level": "DEBUG"}})
    )
    with pytest.raises(ConfigLoadError):
        load_config()


def test_prod_profile_debug_logging_allowed_with_flag(temp_config_dir, caplog, monkeypatch):
    monkeypatch.setenv("APP_PROFILE", "prod")
    (temp_config_dir / "application-prod.yml").write_text(
        yaml.dump({"logging": {"level": "DEBUG"}, "allow_debug_in_prod": True})
    )
    caplog.set_level(logging.WARNING)
    config = load_config()
    assert config["logging"]["level"] == "DEBUG"
    assert "debug logging is enabled in production" in caplog.text.lower()


def test_prod_profile_missing_logging_level_defaults_to_info(temp_config_dir, caplog, monkeypatch):
    """Warn only if logging.level is absent in both base and profile."""
    monkeypatch.setenv("APP_PROFILE", "prod")

    # Base config without logging.level
    (temp_config_dir / "application.yml").write_text(yaml.dump({"app_name": "job-service"}))
    # Prod config also without logging.level
    (temp_config_dir / "application-prod.yml").write_text(yaml.dump({"app_name": "job-service"}))

    caplog.set_level(logging.WARNING, logger="backend.bootstrap.config.config_loader")
    config = load_config()

    assert config["logging"]["level"] == "INFO"
    assert "defaulting to info" in caplog.text.lower()

def test_prod_inherits_logging_level_from_base_without_warning(temp_config_dir, caplog, monkeypatch):
    """If base sets logging.level, prod can inherit without a warning."""
    monkeypatch.setenv("APP_PROFILE", "prod")

    # Base config sets INFO
    (temp_config_dir / "application.yml").write_text(yaml.dump({
        "app_name": "job-service",
        "logging": {"level": "INFO"}
    }))
    # Prod config doesn't override logging.level
    (temp_config_dir / "application-prod.yml").write_text(yaml.dump({"app_name": "job-service"}))

    caplog.set_level(logging.WARNING, logger="backend.bootstrap.config.config_loader")
    config = load_config()

    assert config["logging"]["level"] == "INFO"
    assert "defaulting to info" not in caplog.text.lower()


def test_prod_profile_invalid_logging_level_defaults_to_info(temp_config_dir, caplog, monkeypatch):
    monkeypatch.setenv("APP_PROFILE", "prod")
    (temp_config_dir / "application-prod.yml").write_text(
        yaml.dump({"logging": {"level": "FOOBAR"}})
    )
    caplog.set_level(logging.WARNING)
    config = load_config()
    assert config["logging"]["level"] == "INFO"
    assert "invalid logging.level" in caplog.text.lower()


def test_prod_profile_debug_falls_back_to_info_with_warning(temp_config_dir, caplog, monkeypatch):
    monkeypatch.setenv("APP_PROFILE", "prod")
    (temp_config_dir / "application-prod.yml").write_text(
        yaml.dump({"logging": {"level": "DEBUG"}})
    )
    caplog.set_level(logging.WARNING)
    with pytest.raises(ConfigLoadError):
        load_config()
        
def test_import_merges_additional_config(temp_config_dir, monkeypatch):
    """Import file values override base/profile values."""
    monkeypatch.setenv("APP_PROFILE", "dev")

    # Base config
    (temp_config_dir / "application.yml").write_text(yaml.dump({
        "adapters": {"auth_repository": "MSSQL"}
    }))

    # Dev profile with imports
    (temp_config_dir / "application-dev.yml").write_text(yaml.dump({
        "imports": ["sqlite.yml"]
    }))

    # Imported config file with extra properties
    (temp_config_dir / "sqlite.yml").write_text(yaml.dump({
        "adapters": {"auth_repository": "SQLite"},
        "db": {
            "driver": "sqlite",
            "file": "/tmp/test.sqlite"
        },
        "feature_flags": {
            "enable_fake_db": True
        }
    }))

    config = load_config()

    # Assertions
    assert config["adapters"]["auth_repository"] == "SQLite"
    assert config["db"]["driver"] == "sqlite"
    assert config["db"]["file"] == "/tmp/test.sqlite"
    assert config["feature_flags"]["enable_fake_db"] is True

    # Debug dump for visibility
    import json
    print(json.dumps(config, indent=2))



def test_import_missing_file_warns(temp_config_dir, caplog, monkeypatch):
    """Missing import file should log a warning."""
    caplog.set_level(logging.WARNING)
    monkeypatch.setenv("APP_PROFILE", "dev")

    # Base config
    (temp_config_dir / "application.yml").write_text(yaml.dump({"adapters": {"auth_repository": "MSSQL"}}))

    # Dev profile referencing a missing import
    (temp_config_dir / "application-dev.yml").write_text(yaml.dump({"imports": ["missing.yml"]}))

    config = load_config()
    assert "import file not found" in caplog.text.lower()
        
