# sprig-config-module/tests/test_loader.py
import logging
import tempfile
from pathlib import Path

import pytest
import yaml

from sprigconfig import load_config, deep_merge, ConfigLoadError


@pytest.fixture
def temp_config_dir(monkeypatch):
    """
    Create a temp config dir with a base config and minimal prod/test profiles.
    We intentionally DO NOT create a dev profile so tests can validate dev behavior.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)

        # Base config always present
        base_config = {
            "app_name": "job-service-test",
            # Multiple keys in logging to enable "partial override" warnings
            "logging": {"level": "INFO", "format": "%(message)s"},
            "suppress_config_merge_warnings": False,
        }
        (config_dir / "application.yml").write_text(yaml.dump(base_config))

        # Minimal prod & test profile files (tests that require "missing" will remove them)
        (config_dir / "application-prod.yml").write_text(
            yaml.dump({"server": {"port": 8000}, "logging": {"level": "WARN"}, "feature": {"dummy_flag": True}})
        )
        (config_dir / "application-test.yml").write_text(
            yaml.dump({"server": {"port": 8000}, "logging": {"level": "WARN"}, "feature": {"dummy_flag": True}})
        )

        # Point loader to this temp directory
        monkeypatch.setenv("APP_CONFIG_DIR", str(config_dir))

        yield config_dir


def test_dev_profile_missing_config_warns_and_continues(caplog, temp_config_dir, monkeypatch, maybe_dump):
    caplog.set_level(logging.INFO, logger="sprigconfig.loader")
    monkeypatch.setenv("APP_PROFILE", "dev")
    # Intentionally no application-dev.yml
    config = load_config()
    assert config["logging"]["level"] == "INFO"
    assert "continuing with base config" in caplog.text.lower()

    maybe_dump(config)


def test_prod_profile_missing_config_fails(temp_config_dir, monkeypatch):
    monkeypatch.setenv("APP_PROFILE", "prod")
    # Remove profile file to force failure
    prod_file = temp_config_dir / "application-prod.yml"
    if prod_file.exists():
        prod_file.unlink()
    with pytest.raises(ConfigLoadError):
        load_config()


def test_test_profile_missing_config_fails(temp_config_dir, monkeypatch):
    monkeypatch.setenv("APP_PROFILE", "test")
    # Remove profile file to force failure
    test_file = temp_config_dir / "application-test.yml"
    if test_file.exists():
        test_file.unlink()
    with pytest.raises(ConfigLoadError):
        load_config()


def test_merge_warns_on_partial_override(temp_config_dir, caplog, monkeypatch):
    caplog.set_level(logging.WARNING, logger="sprigconfig.loader")
    monkeypatch.setenv("APP_PROFILE", "dev")

    # Override missing some keys in logging to trigger partial override warning
    override_config = {"logging": {"level": "DEBUG"}}
    (temp_config_dir / "application-dev.yml").write_text(yaml.dump(override_config))

    load_config()
    assert "partially overridden" in caplog.text.lower()


def test_merge_suppresses_warning_when_flag_set(temp_config_dir, caplog, monkeypatch):
    caplog.set_level(logging.WARNING, logger="sprigconfig.loader")
    monkeypatch.setenv("APP_PROFILE", "dev")

    override_config = {
        "logging": {"level": "DEBUG"},
        "suppress_config_merge_warnings": True,
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


def test_prod_debug_logging_allowed_with_flag(temp_config_dir, monkeypatch, maybe_dump):
    monkeypatch.setenv("APP_PROFILE", "prod")
    (temp_config_dir / "application-prod.yml").write_text(
        yaml.dump({"logging": {"level": "DEBUG"}, "allow_debug_in_prod": True})
    )
    config = load_config()
    assert config["logging"]["level"] == "DEBUG"

    maybe_dump(config)


def test_prod_profile_debug_logging_disallowed(temp_config_dir, monkeypatch):
    monkeypatch.setenv("APP_PROFILE", "prod")
    (temp_config_dir / "application-prod.yml").write_text(
        yaml.dump({"logging": {"level": "DEBUG"}})
    )
    with pytest.raises(ConfigLoadError):
        load_config()

def test_prod_profile_debug_logging_allowed_with_flag(temp_config_dir, caplog, monkeypatch, maybe_dump):
    monkeypatch.setenv("APP_PROFILE", "prod")
    (temp_config_dir / "application-prod.yml").write_text(
        yaml.dump({"logging": {"level": "DEBUG"}, "allow_debug_in_prod": True})
    )
    caplog.set_level(logging.WARNING, logger="sprigconfig.loader")
    config = load_config()
    assert config["logging"]["level"] == "DEBUG"
    assert "debug logging is enabled in production" in caplog.text.lower()

    maybe_dump(config)


def test_prod_profile_missing_logging_level_defaults_to_info(temp_config_dir, caplog, monkeypatch, maybe_dump):
    """Warn only if logging.level is absent in both base and profile."""
    monkeypatch.setenv("APP_PROFILE", "prod")

    # Base config without logging.level
    (temp_config_dir / "application.yml").write_text(yaml.dump({"app_name": "job-service"}))
    # Prod config also without logging.level
    (temp_config_dir / "application-prod.yml").write_text(yaml.dump({"app_name": "job-service"}))

    caplog.set_level(logging.WARNING, logger="sprigconfig.loader")
    config = load_config()

    assert config["logging"]["level"] == "INFO"
    assert "defaulting to info" in caplog.text.lower()

    maybe_dump(config)


def test_prod_inherits_logging_level_from_base_without_warning(temp_config_dir, caplog, monkeypatch, maybe_dump):
    """If base sets logging.level, prod can inherit without a warning."""
    monkeypatch.setenv("APP_PROFILE", "prod")

    # Base config sets INFO
    (temp_config_dir / "application.yml").write_text(
        yaml.dump({"app_name": "job-service", "logging": {"level": "INFO"}})
    )
    # Prod config doesn't override logging.level
    (temp_config_dir / "application-prod.yml").write_text(yaml.dump({"app_name": "job-service"}))

    caplog.set_level(logging.WARNING, logger="sprigconfig.loader")
    config = load_config()

    assert config["logging"]["level"] == "INFO"
    assert "defaulting to info" not in caplog.text.lower()

    maybe_dump(config)

def test_prod_profile_invalid_logging_level_defaults_to_info(temp_config_dir, caplog, monkeypatch, maybe_dump):
    monkeypatch.setenv("APP_PROFILE", "prod")
    (temp_config_dir / "application-prod.yml").write_text(
        yaml.dump({"logging": {"level": "FOOBAR"}})
    )
    caplog.set_level(logging.WARNING, logger="sprigconfig.loader")
    config = load_config()
    assert config["logging"]["level"] == "INFO"
    assert "invalid logging.level" in caplog.text.lower()
    maybe_dump(config)


def test_prod_profile_debug_falls_back_to_info_with_warning(temp_config_dir, caplog, monkeypatch):
    monkeypatch.setenv("APP_PROFILE", "prod")
    (temp_config_dir / "application-prod.yml").write_text(
        yaml.dump({"logging": {"level": "DEBUG"}})
    )
    caplog.set_level(logging.WARNING, logger="sprigconfig.loader")
    with pytest.raises(ConfigLoadError):
        load_config()


def test_import_merges_additional_config(temp_config_dir, monkeypatch, maybe_dump):
    """Import file values override base/profile values."""
    monkeypatch.setenv("APP_PROFILE", "dev")

    # Base config
    (temp_config_dir / "application.yml").write_text(
        yaml.dump({"adapters": {"auth_repository": "MSSQL"}})
    )

    # Dev profile with imports
    (temp_config_dir / "application-dev.yml").write_text(
        yaml.dump({"imports": ["sqlite.yml"]})
    )

    # Imported config file with extra properties
    (temp_config_dir / "sqlite.yml").write_text(
        yaml.dump(
            {
                "adapters": {"auth_repository": "SQLite"},
                "db": {"driver": "sqlite", "file": "/tmp/test.sqlite"},
                "feature_flags": {"enable_fake_db": True},
            }
        )
    )

    config = load_config()

    # Assertions
    assert config["adapters"]["auth_repository"] == "SQLite"
    assert config["db"]["driver"] == "sqlite"
    assert config["db"]["file"] == "/tmp/test.sqlite"
    assert config["feature_flags"]["enable_fake_db"] is True

    maybe_dump(config)


def test_import_missing_file_warns(temp_config_dir, caplog, monkeypatch):
    """Missing import file should log a warning."""
    caplog.set_level(logging.WARNING, logger="sprigconfig.loader")
    monkeypatch.setenv("APP_PROFILE", "dev")

    # Base config
    (temp_config_dir / "application.yml").write_text(
        yaml.dump({"adapters": {"auth_repository": "MSSQL"}})
    )

    # Dev profile referencing a missing import
    (temp_config_dir / "application-dev.yml").write_text(
        yaml.dump({"imports": ["missing.yml"]})
    )

    load_config()
    assert "import file not found" in caplog.text.lower()


def test_injects_app_profile(temp_config_dir, monkeypatch, maybe_dump):
    """Loader should inject APP_PROFILE into the merged config (app.profile)."""
    monkeypatch.setenv("APP_PROFILE", "dev")
    cfg = load_config()
    # If your loader injects under a different key, adjust this assertion accordingly.
    assert cfg["app"]["profile"] == "dev"
    maybe_dump(cfg)

def test_file_profile_conflict_warns_and_runtime_wins(temp_config_dir, caplog, monkeypatch, maybe_dump):
    caplog.set_level(logging.WARNING)
    (temp_config_dir / "application.yml").write_text("app:\n  profile: wrong\n")
    monkeypatch.setenv("APP_PROFILE", "dev")
    cfg = load_config()
    assert cfg["app"]["profile"] == "dev"
    assert "Ignoring app.profile" in caplog.text
    maybe_dump(cfg)
