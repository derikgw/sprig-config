# sprigconfig/config_singleton.py
"""
Thread-safe global configuration singleton.

Provides:

    ConfigSingleton.get(profile, config_dir)
    ConfigSingleton.reload(profile, config_dir)
    ConfigSingleton._clear_all()   (used by test fixtures)

Each unique (profile, config_dir) pair maps to a single cached Config instance.

ConfigLoader produces the actual Config object.
"""

from pathlib import Path
import threading

from .config_loader import ConfigLoader
from .config import Config
from .exceptions import ConfigLoadError


class ConfigSingleton:
    """
    Global singleton manager for SprigConfig.

    Cache key: (absolute config_dir, profile)

    Thread-safe using a global lock.
    """

    # Maps: (dir, profile) -> Config instance
    _cache = {}

    # Thread lock for thread-safe operations
    _lock = threading.Lock()

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    @classmethod
    def get(cls, *, profile: str, config_dir: Path):
        """
        Return cached Config for (config_dir, profile).
        If missing, load using ConfigLoader and cache it.
        """
        key = cls._make_key(profile, config_dir)

        with cls._lock:
            if key not in cls._cache:
                loader = ConfigLoader(config_dir=config_dir, profile=profile)
                cfg = loader.load()
                if not isinstance(cfg, Config):
                    raise ConfigLoadError("ConfigLoader.load() must return Config")

                cls._cache[key] = cfg

            return cls._cache[key]

    @classmethod
    def reload(cls, *, profile: str, config_dir: Path):
        """
        Force reload of config for the given profile + directory.
        Always returns a NEW instance.
        """
        key = cls._make_key(profile, config_dir)

        with cls._lock:
            loader = ConfigLoader(config_dir=config_dir, profile=profile)
            cfg = loader.load()
            if not isinstance(cfg, Config):
                raise ConfigLoadError("ConfigLoader.load() must return Config")

            cls._cache[key] = cfg
            return cfg

    @classmethod
    def _clear_all(cls):
        """
        Clear the entire singleton cache.
        Used exclusively by test fixtures.
        """
        with cls._lock:
            cls._cache.clear()

    # ------------------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------------------

    @staticmethod
    def _make_key(profile: str, config_dir: Path):
        """
        Normalize profile + directory into a hashable tuple key.
        """
        dir_path = Path(config_dir).resolve()
        return (str(dir_path), profile)
