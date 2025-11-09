# tests/test_loader.py
# sprig-config-module/tests/test_loader.py
import logging
import tempfile
from pathlib import Path
import pytest
import yaml

from sprigconfig import load_config, deep_merge, ConfigLoadError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_config_dir(monkeypatch):
    """
    Create a temporary config dir with base + minimal prod/test profiles.
    Dev profile is intentionally omitted so missing-profile logic can be tested.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)

        # Base config
        base_config = {
            "app_name": "job-service-test",
            "logging": {"level": "INFO", "format": "%(message)s"},
            "suppress_config_merge_warnings": False,
        }
        (config_dir / "application.yml").write_text(yaml.dump(base_config))

        # Minimal prod/test configs
        (config_dir / "application-prod.yml").write_text(
            yaml.dump({"server": {"port": 8000}, "logging": {"level": "WARN"}})
        )
        (config_dir / "application-test.yml").write_text(
            yaml.dump({"server": {"port": 8001}, "logging": {"level": "WARN"}})
        )

        monkeypatch.setenv("APP_CONFIG_DIR", str(config_dir))
        yield config_dir


@pytest.fixture
def load_test_config():
    """Wrapper fixture to call load_config with explicit args."""
    def _load(profile=None, config_dir=None):
        from os import getenv
        from pathlib import Path
        profile = profile or getenv("APP_PROFILE", "dev")
        config_dir = config_dir or Path(getenv("APP_CONFIG_DIR", Path.cwd() / "config"))
        return load_config(profile=profile, config_dir=config_dir)
    return _load


@pytest.fixture
def load_raw_config():
    """Direct alias to load_config for explicit profile+dir tests."""
    return load_config


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_dev_profile_missing_config_warns_and_continues(caplog, temp_config_dir, maybe_dump, load_test_config):
    caplog.set_level(logging.INFO, logger="sprigconfig.loader")
    config = load_test_config(profile="dev", config_dir=temp_config_dir)
    assert config["logging"]["level"] == "INFO"
    assert "continuing with base config" in caplog.text.lower()
    maybe_dump(config)


def test_prod_profile_missing_config_fails(tmp_path, load_raw_config):
    """Production profile must fail if its config file is missing."""
    empty_dir = tmp_path / "config"
    empty_dir.mkdir()
    with pytest.raises(ConfigLoadError):
        load_raw_config(profile="prod", config_dir=empty_dir)

def test_merge_warns_on_partial_override(temp_config_dir, caplog, load_test_config):
    caplog.set_level(logging.WARNING, logger="sprigconfig.loader")
    override = {"logging": {"level": "DEBUG"}}
    (temp_config_dir / "application-dev.yml").write_text(yaml.dump(override))
    load_test_config(profile="dev", config_dir=temp_config_dir)
    assert "partially overridden" in caplog.text.lower()


def test_merge_suppresses_warning_when_flag_set(temp_config_dir, caplog, load_test_config):
    caplog.set_level(logging.WARNING, logger="sprigconfig.loader")
    override = {
        "logging": {"level": "DEBUG"},
        "suppress_config_merge_warnings": True,
    }
    (temp_config_dir / "application-dev.yml").write_text(yaml.dump(override))
    load_test_config(profile="dev", config_dir=temp_config_dir)
    assert "partially overridden" not in caplog.text.lower()


def test_deep_merge_overrides_and_adds():
    base = {"server": {"port": 8000, "threads": 4}}
    override = {"server": {"threads": 8}, "feature": {"x": True}}
    merged = deep_merge(base, override, suppress_warnings=True)
    assert merged["server"]["threads"] == 8
    assert merged["server"]["port"] == 8000
    assert merged["feature"]["x"] is True


def test_invalid_yaml_raises_clear_error(temp_config_dir, load_test_config):
    (temp_config_dir / "application-prod.yml").write_text("logging: : : : broken")
    with pytest.raises(ConfigLoadError):
        load_test_config(profile="prod", config_dir=temp_config_dir)


def test_prod_debug_logging_allowed_with_flag(temp_config_dir, maybe_dump, load_test_config):
    (temp_config_dir / "application-prod.yml").write_text(
        yaml.dump({"logging": {"level": "DEBUG"}, "allow_debug_in_prod": True})
    )
    config = load_test_config(profile="prod", config_dir=temp_config_dir)
    assert config["logging"]["level"] == "DEBUG"
    maybe_dump(config)


def test_prod_profile_debug_logging_allowed_with_flag(temp_config_dir, caplog, maybe_dump, load_test_config):
    caplog.set_level(logging.WARNING, logger="sprigconfig.loader")
    (temp_config_dir / "application-prod.yml").write_text(
        yaml.dump({"logging": {"level": "DEBUG"}, "allow_debug_in_prod": True})
    )
    config = load_test_config(profile="prod", config_dir=temp_config_dir)
    assert config["logging"]["level"] == "DEBUG"
    assert "debug logging is enabled in production" in caplog.text.lower()
    maybe_dump(config)


def test_prod_profile_missing_logging_level_defaults_to_info(temp_config_dir, caplog, maybe_dump, load_test_config):
    """Warn only if logging.level is absent in both base and profile."""
    (temp_config_dir / "application.yml").write_text(yaml.dump({"app_name": "job-service"}))
    (temp_config_dir / "application-prod.yml").write_text(yaml.dump({"app_name": "job-service"}))
    caplog.set_level(logging.WARNING, logger="sprigconfig.loader")
    config = load_test_config(profile="prod", config_dir=temp_config_dir)
    assert config["logging"]["level"] == "INFO"
    assert "defaulting to info" in caplog.text.lower()
    maybe_dump(config)


def test_prod_inherits_logging_level_from_base_without_warning(temp_config_dir, caplog, maybe_dump, load_test_config):
    """If base sets logging.level, prod can inherit without warning."""
    (temp_config_dir / "application.yml").write_text(
        yaml.dump({"app_name": "job-service", "logging": {"level": "INFO"}})
    )
    (temp_config_dir / "application-prod.yml").write_text(yaml.dump({"app_name": "job-service"}))
    caplog.set_level(logging.WARNING, logger="sprigconfig.loader")
    config = load_test_config(profile="prod", config_dir=temp_config_dir)
    assert config["logging"]["level"] == "INFO"
    assert "defaulting to info" not in caplog.text.lower()
    maybe_dump(config)


def test_prod_profile_invalid_logging_level_defaults_to_info(temp_config_dir, caplog, maybe_dump, load_test_config):
    (temp_config_dir / "application-prod.yml").write_text(
        yaml.dump({"logging": {"level": "FOOBAR"}})
    )
    caplog.set_level(logging.WARNING, logger="sprigconfig.loader")
    config = load_test_config(profile="prod", config_dir=temp_config_dir)
    assert config["logging"]["level"] == "INFO"
    assert "invalid logging.level" in caplog.text.lower()
    maybe_dump(config)


def test_import_merges_additional_config(temp_config_dir, maybe_dump, load_test_config):
    """Import file values override base/profile values."""
    (temp_config_dir / "application.yml").write_text(
        yaml.dump({"adapters": {"auth_repository": "MSSQL"}})
    )
    (temp_config_dir / "application-dev.yml").write_text(
        yaml.dump({"imports": ["sqlite.yml"]})
    )
    (temp_config_dir / "sqlite.yml").write_text(
        yaml.dump({
            "adapters": {"auth_repository": "SQLite"},
            "db": {"driver": "sqlite", "file": "/tmp/test.sqlite"},
            "feature_flags": {"enable_fake_db": True},
        })
    )
    config = load_test_config(profile="dev", config_dir=temp_config_dir)
    assert config["adapters"]["auth_repository"] == "SQLite"
    assert config["db"]["driver"] == "sqlite"
    assert config["db"]["file"] == "/tmp/test.sqlite"
    assert config["feature_flags"]["enable_fake_db"] is True
    maybe_dump(config)


def test_import_missing_file_warns(temp_config_dir, caplog, load_test_config):
    """Missing import file should log a warning."""
    caplog.set_level(logging.WARNING, logger="sprigconfig.loader")
    (temp_config_dir / "application.yml").write_text(
        yaml.dump({"adapters": {"auth_repository": "MSSQL"}})
    )
    (temp_config_dir / "application-dev.yml").write_text(
        yaml.dump({"imports": ["missing.yml"]})
    )
    load_test_config(profile="dev", config_dir=temp_config_dir)
    assert "import file not found" in caplog.text.lower()


def test_injects_app_profile(temp_config_dir, maybe_dump, load_test_config):
    """Loader should inject APP_PROFILE into the merged config (app.profile)."""
    cfg = load_test_config(profile="dev", config_dir=temp_config_dir)
    assert cfg["app"]["profile"] == "dev"
    maybe_dump(cfg)


def test_file_profile_conflict_warns_and_runtime_wins(temp_config_dir, caplog, maybe_dump, load_test_config):
    caplog.set_level(logging.WARNING)
    (temp_config_dir / "application.yml").write_text("app:\n  profile: wrong\n")
    cfg = load_test_config(profile="dev", config_dir=temp_config_dir)
    assert cfg["app"]["profile"] == "dev"
    assert "ignoring app.profile" in caplog.text.lower()
    maybe_dump(cfg)
