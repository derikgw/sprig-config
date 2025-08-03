import pytest
from pathlib import Path
import sprigconfig
from sprigconfig.loader import load_config


def test_loads_base_config(tmp_path):
    """
    GIVEN a minimal application.yml
    WHEN load_config() is called
    THEN the returned dict should match the file contents
    """
    # Arrange
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "application.yml"
    config_file.write_text("""
app:
  name: testapp
  version: 1.0
""")

    # Act
    config = load_config(config_dir=config_dir)

    # Assert
    assert config["app"]["name"] == "testapp"
    assert config["app"]["version"] == 1.0
