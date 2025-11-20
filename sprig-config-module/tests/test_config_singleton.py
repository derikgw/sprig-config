# tests/test_config_singleton.py
"""
Tests for the future ConfigSingleton class.

EXPECTED BEHAVIOR:

- ConfigSingleton.get(profile, config_dir) returns a Config instance.
- The same (profile, config_dir) pair always returns the same instance.
- Different profiles or directories produce different instances.
- Must be thread-safe: concurrent calls return the same instance.
- Must allow an explicit reload() to rebuild the Config.
- Must integrate with Config (dotted-key access, secret safety, etc.).
- load_config() remains backward compatible, but ConfigSingleton is the
  new "global config" option.

All of these tests WILL FAIL until ConfigSingleton is implemented.
"""

import threading
from pathlib import Path
import pytest

from sprigconfig import (
    ConfigLoader,
    ConfigSingleton,
    Config,
    load_config,       # backward-compatible
    ConfigLoadError,
)


# ----------------------------------------------------------------------
# FIXTURES
# ----------------------------------------------------------------------

@pytest.fixture
def config_dir(use_real_config_dir):
    """Use the real tests/config directory."""
    return use_real_config_dir


@pytest.fixture
def singleton():
    """
    Helper: clears singleton state before each test.
    """
    ConfigSingleton._clear_all()  # WILL FAIL until implemented
    return ConfigSingleton


# ----------------------------------------------------------------------
# BASIC SINGLETON BEHAVIOR
# ----------------------------------------------------------------------

def test_singleton_returns_config_instance(singleton, config_dir):
    cfg = singleton.get(profile="dev", config_dir=config_dir)
    assert isinstance(cfg, Config)


def test_singleton_same_instance_for_same_profile_and_dir(singleton, config_dir):
    cfg1 = singleton.get(profile="dev", config_dir=config_dir)
    cfg2 = singleton.get(profile="dev", config_dir=config_dir)
    assert cfg1 is cfg2


def test_singleton_different_profiles_are_unique_instances(singleton, config_dir):
    cfg1 = singleton.get(profile="dev", config_dir=config_dir)
    cfg2 = singleton.get(profile="prod", config_dir=config_dir)
    assert cfg1 is not cfg2


def test_singleton_different_config_dirs_are_unique(singleton, tmp_path, config_dir):
    cfg1 = singleton.get(profile="dev", config_dir=config_dir)
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    (other_dir / "application.yml").write_text("app:\n  name: otherapp\n")
    cfg2 = singleton.get(profile="dev", config_dir=other_dir)
    assert cfg1 is not cfg2


# ----------------------------------------------------------------------
# THREAD-SAFETY TEST
# ----------------------------------------------------------------------

def test_singleton_thread_safety(singleton, config_dir):
    """
    Two threads calling get() simultaneously must receive the same instance.
    """

    results = []

    def worker():
        cfg = singleton.get(profile="dev", config_dir=config_dir)
        results.append(cfg)

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start(), t2.start()
    t1.join(), t2.join()

    assert results[0] is results[1]


# ----------------------------------------------------------------------
# RELOAD BEHAVIOR
# ----------------------------------------------------------------------

def test_singleton_reload_replaces_instance(singleton, config_dir):
    """
    reload(profile, config_dir) must force a fresh load.
    """
    cfg1 = singleton.get(profile="dev", config_dir=config_dir)
    cfg2 = singleton.reload(profile="dev", config_dir=config_dir)

    assert isinstance(cfg2, Config)
    assert cfg2 is not cfg1


def test_reload_only_affects_specified_profile(singleton, config_dir):
    dev_cfg = singleton.get(profile="dev", config_dir=config_dir)
    prod_cfg = singleton.get(profile="prod", config_dir=config_dir)

    # Reload only dev
    new_dev_cfg = singleton.reload(profile="dev", config_dir=config_dir)

    assert new_dev_cfg is not dev_cfg
    assert prod_cfg is singleton.get(profile="prod", config_dir=config_dir)


# ----------------------------------------------------------------------
# DOTTED-KEY ACCESS PROXY
# ----------------------------------------------------------------------

def test_singleton_provides_dotted_key_access(singleton, config_dir):
    """
    ConfigSingleton.get(...) returns Config, so dotted-key access must work.
    """
    cfg = singleton.get(profile="dev", config_dir=config_dir)
    assert cfg.get("logging.level") == "INFO"


# ----------------------------------------------------------------------
# SECRET HANDLING THROUGH SINGLETON
# ----------------------------------------------------------------------

def test_singleton_preserves_lazysecret_objects(singleton, config_dir):
    cfg = singleton.get(profile="secrets", config_dir=config_dir)
    secret = cfg.get("secrets.api_key")
    assert hasattr(secret, "is_secret") or isinstance(secret, object)


# ----------------------------------------------------------------------
# BACKWARD COMPAT: load_config() and singleton coexist
# ----------------------------------------------------------------------

def test_load_config_independent_of_singleton(singleton, config_dir):
    """
    load_config() must NOT use the same instance as ConfigSingleton.get().
    They are separate code paths.
    """
    cfg1 = singleton.get(profile="dev", config_dir=config_dir)
    cfg2 = load_config(profile="dev", config_dir=config_dir)

    assert isinstance(cfg1, Config)
    assert isinstance(cfg2, Config)
    assert cfg1 is not cfg2


# ----------------------------------------------------------------------
# CLEAR ALL / RESET
# ----------------------------------------------------------------------

def test_singleton_clear_all_resets_state(singleton, config_dir):
    """
    _clear_all() should clear the entire internal cache.
    """
    cfg1 = singleton.get(profile="dev", config_dir=config_dir)

    singleton._clear_all()
    cfg2 = singleton.get(profile="dev", config_dir=config_dir)

    assert cfg1 is not cfg2
