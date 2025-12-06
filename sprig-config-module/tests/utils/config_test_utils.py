# tests/utils/config_test_utils.py

from sprigconfig.config_singleton import ConfigSingleton
from pathlib import Path

def reload_for_testing(*, profile: str, config_dir: Path):
    """
    Test-only helper: fully resets and reloads ConfigSingleton.
    """
    ConfigSingleton._clear_all()
    return ConfigSingleton.initialize(profile=profile, config_dir=config_dir)
