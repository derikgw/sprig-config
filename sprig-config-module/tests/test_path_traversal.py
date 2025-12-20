"""
Test path traversal protection in import resolution.
"""
import pytest
from pathlib import Path
from sprigconfig.config_loader import ConfigLoader
from sprigconfig.exceptions import ConfigLoadError


def test_path_traversal_blocked(tmp_path):
    """
    Importing with ../ that escapes config_dir should raise ConfigLoadError.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Create a malicious config that tries to traverse up
    malicious_config = config_dir / "application.yml"
    malicious_config.write_text("""
app:
  name: Test

imports:
  - ../../etc/passwd
""")

    with pytest.raises(ConfigLoadError, match="Path traversal detected"):
        ConfigLoader(config_dir=config_dir, profile="dev").load()


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
