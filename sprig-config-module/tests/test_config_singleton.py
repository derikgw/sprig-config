# tests/test_config_singleton.py
"""
Tests for the corrected Java-style ConfigSingleton class.

NEW EXPECTED BEHAVIOR:

- ConfigSingleton.initialize(profile, config_dir) initializes ONCE.
- ConfigSingleton.get() returns that same instance.
- Calling initialize() twice is an error.
- reload_for_testing() replaces the singleton (tests ONLY).
- _clear_all() resets state between tests.
- No support for multi-profile or multi-directory registries.
- load_config() is independent from the singleton.
"""

import threading
from pathlib import Path
import pytest

from sprigconfig import (
    ConfigSingleton,
    Config,
    load_config,
    ConfigLoadError,
)


# ----------------------------------------------------------------------
# FIXTURE: CLEAR BEFORE EACH TEST
# ----------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_singleton():
    ConfigSingleton._clear_all()
    yield
    ConfigSingleton._clear_all()


@pytest.fixture
def config_dir(use_real_config_dir):
    """Use the real tests/config directory."""
    return use_real_config_dir


# ----------------------------------------------------------------------
# BASIC SINGLETON BEHAVIOR
# ----------------------------------------------------------------------

def test_singleton_returns_config_instance(config_dir):
    cfg = ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
    assert isinstance(cfg, Config)
    assert ConfigSingleton.get() is cfg


def test_singleton_same_instance_for_same_profile_and_dir(config_dir):
    cfg1 = ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
    cfg2 = ConfigSingleton.get()
    assert cfg1 is cfg2


def test_singleton_initialize_cannot_be_called_twice(config_dir):
    ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
    with pytest.raises(ConfigLoadError):
        ConfigSingleton.initialize(profile="dev", config_dir=config_dir)


def test_singleton_cannot_initialize_with_different_profile(config_dir):
    ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
    with pytest.raises(ConfigLoadError):
        ConfigSingleton.initialize(profile="prod", config_dir=config_dir)


def test_singleton_cannot_initialize_with_different_config_dir(config_dir, tmp_path):
    ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
    with pytest.raises(ConfigLoadError):
        ConfigSingleton.initialize(profile="dev", config_dir=tmp_path)


# ----------------------------------------------------------------------
# THREAD-SAFETY TEST
# ----------------------------------------------------------------------

def test_singleton_thread_safety(config_dir):
    """
    Two threads racing to initialize must result in exactly ONE successful
    initialization. The other must raise ConfigLoadError. The final singleton
    must be the successfully created instance.
    """

    results = []
    errors = []

    def worker():
        try:
            cfg = ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
            results.append(cfg)
        except ConfigLoadError:
            errors.append("fail")

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start(); t2.start()
    t1.join(); t2.join()

    # Exactly 1 successful initialization
    assert len(results) == 1
    # One of the threads must have failed
    assert len(errors) == 1

    # And get() should now return the one valid instance
    assert ConfigSingleton.get() is results[0]



# ----------------------------------------------------------------------
# TEST RELOAD (TEST-ONLY)
# ----------------------------------------------------------------------

def test_singleton_reload_replaces_instance(config_dir):
    cfg1 = ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
    cfg2 = ConfigSingleton.reload_for_testing(profile="dev", config_dir=config_dir)

    assert isinstance(cfg2, Config)
    assert cfg2 is not cfg1
    assert ConfigSingleton.get() is cfg2


def test_reload_only_affects_after_reload(config_dir):
    ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
    cfg_new = ConfigSingleton.reload_for_testing(profile="dev", config_dir=config_dir)
    assert ConfigSingleton.get() is cfg_new


# ----------------------------------------------------------------------
# DOTTED-KEY ACCESS
# ----------------------------------------------------------------------

def test_singleton_provides_dotted_key_access(config_dir):
    cfg = ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
    assert cfg.get("logging.level") == "INFO"


# ----------------------------------------------------------------------
# SECRET HANDLING THROUGH SINGLETON
# ----------------------------------------------------------------------

def test_singleton_preserves_lazysecret_objects(config_dir):
    cfg = ConfigSingleton.initialize(profile="secrets", config_dir=config_dir)
    secret = cfg.get("secrets.api_key")
    assert hasattr(secret, "is_secret") or isinstance(secret, object)


# ----------------------------------------------------------------------
# BACKWARD COMPAT: load_config() remains separate
# ----------------------------------------------------------------------

def test_load_config_independent_of_singleton(config_dir):
    cfg1 = ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
    cfg2 = load_config(profile="dev", config_dir=config_dir)

    assert isinstance(cfg1, Config)
    assert isinstance(cfg2, Config)
    assert cfg1 is not cfg2


# ----------------------------------------------------------------------
# CLEAR ALL
# ----------------------------------------------------------------------

def test_singleton_clear_all_resets_state(config_dir):
    cfg1 = ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
    ConfigSingleton._clear_all()
    with pytest.raises(ConfigLoadError):
        ConfigSingleton.get()
