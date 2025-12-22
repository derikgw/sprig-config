"""
Test TOML format support in ConfigLoader.
"""
import pytest
from pathlib import Path
from sprigconfig.config_loader import ConfigLoader


def test_toml_basic_loading(tmp_path):
    """
    Test that basic TOML config files can be loaded.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Create TOML config
    toml_config = config_dir / "application.toml"
    toml_config.write_text("""
[app]
name = "TestApp"
version = "1.0.0"

[server]
host = "localhost"
port = 8080
""")

    cfg = ConfigLoader(config_dir=config_dir, profile="dev", config_format="toml").load()

    assert cfg.get("app.name") == "TestApp"
    assert cfg.get("app.version") == "1.0.0"
    assert cfg.get("server.host") == "localhost"
    assert cfg.get("server.port") == 8080


def test_toml_with_imports(tmp_path):
    """
    Test that TOML imports work correctly.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    imports_dir = config_dir / "imports"
    imports_dir.mkdir()

    # Create base TOML config
    # Note: imports must be at root level in TOML
    base_config = config_dir / "application.toml"
    base_config.write_text("""
imports = ["imports/database"]

[app]
name = "TestApp"
""")

    # Create imported TOML file
    db_config = imports_dir / "database.toml"
    db_config.write_text("""
[database]
host = "localhost"
port = 5432
name = "testdb"
""")

    cfg = ConfigLoader(config_dir=config_dir, profile="dev", config_format="toml").load()

    assert cfg.get("app.name") == "TestApp"
    assert cfg.get("database.host") == "localhost"
    assert cfg.get("database.port") == 5432
    assert cfg.get("database.name") == "testdb"


def test_toml_profile_overlay(tmp_path):
    """
    Test that TOML profile overlays work correctly.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Create base TOML config
    base_config = config_dir / "application.toml"
    base_config.write_text("""
[server]
host = "0.0.0.0"
port = 8080

[logging]
level = "INFO"
""")

    # Create dev profile overlay
    dev_config = config_dir / "application-dev.toml"
    dev_config.write_text("""
[server]
host = "localhost"

[logging]
level = "DEBUG"
""")

    cfg = ConfigLoader(config_dir=config_dir, profile="dev", config_format="toml").load()

    # Profile should override base values
    assert cfg.get("server.host") == "localhost"
    assert cfg.get("server.port") == 8080
    assert cfg.get("logging.level") == "DEBUG"


def test_toml_env_var_expansion(tmp_path, monkeypatch):
    """
    Test that environment variable expansion works in TOML files.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    monkeypatch.setenv("TEST_PORT", "9000")
    monkeypatch.setenv("TEST_HOST", "example.com")

    # Create TOML config with env vars
    toml_config = config_dir / "application.toml"
    toml_config.write_text("""
[server]
host = "${TEST_HOST}"
port = "${TEST_PORT}"
fallback = "${MISSING_VAR:default_value}"
""")

    cfg = ConfigLoader(config_dir=config_dir, profile="dev", config_format="toml").load()

    assert cfg.get("server.host") == "example.com"
    assert cfg.get("server.port") == "9000"
    assert cfg.get("server.fallback") == "default_value"
