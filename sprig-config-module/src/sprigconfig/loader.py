# sprigconfig/loader.py
"""
Backward-compatible loader shim.

This file exists solely to preserve the old import path:

    from sprigconfig.loader import load_config

or

    from sprigconfig import load_config

The REAL implementation now lives in:

    sprigconfig/config_loader.py

This shim simply delegates to ConfigLoader and returns a Config object.
"""

from pathlib import Path

from .config_loader import ConfigLoader
from .config import Config
from .exceptions import ConfigLoadError


def load_config(*, profile: str, config_dir: Path = None) -> Config:
    """
    Legacy entrypoint for SprigConfig users.

    Arguments:
        profile (str): active config profile name ("dev", "prod", etc.)
        config_dir (Path|None): directory containing application.yml,
                                application-<profile>.yml, and any imports.

    Returns:
        Config: the final merged configuration object.

    This function simply forwards to the new ConfigLoader.
    It exists to maintain backward compatibility.
    """

    loader = ConfigLoader(config_dir=config_dir, profile=profile)
    cfg = loader.load()

    if not isinstance(cfg, Config):
        raise ConfigLoadError(
            "ConfigLoader.load() must return a Config instance for backward compatibility"
        )

    return cfg


__all__ = ["load_config"]
