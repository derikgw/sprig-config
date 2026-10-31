"""Functional tests for ordinary in-directory subdirectory imports."""

from sprigconfig.config_loader import ConfigLoader


def test_normal_subdirectory_imports_allowed(tmp_path):
    """
    Imports within subdirectories of config_dir should work fine.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    imports_dir = config_dir / "imports"
    imports_dir.mkdir()

    # Create base config
    base_config = config_dir / "application.yml"
    base_config.write_text("""
app:
  name: Test

imports:
  - imports/common
""")

    # Create imported file
    common_config = imports_dir / "common.yml"
    common_config.write_text("""
server:
  port: 8080
""")

    # Should not raise
    cfg = ConfigLoader(config_dir=config_dir, profile="dev").load()
    assert cfg.get("server.port") == 8080
