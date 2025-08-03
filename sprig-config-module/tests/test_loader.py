import pytest
from sprigconfig.loader import load_config


def test_loads_base_config(tmp_path):
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    (cfg_dir / "application.yml").write_text("app:\n  name: testapp")

    config = load_config(config_dir=cfg_dir)
    assert config["app"]["name"] == "testapp"
