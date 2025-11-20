# tests/test_integration.py
"""
Full-system integration tests for the new SprigConfig architecture.

These tests do not test small units. They validate that:

    - ConfigLoader, Config, deep merge, imports, profiles,
      and LazySecret behavior work cohesively.

    - load_config() (legacy API) cooperates with new classes.

    - ConfigSingleton operates independently and does not interfere
      with normal loading.

    - Environment-based defaults (APP_CONFIG_DIR) work.

    - Debug-dump integration works through capture_config() fixture.

This is the final TDD layer — all top-level behavior must pass here.
"""

import os
import yaml
from pathlib import Path
import pytest

from sprigconfig import (
    load_config,
    ConfigLoader,
    ConfigSingleton,
    Config,
    ConfigLoadError,
)
from sprigconfig.lazy_secret import LazySecret


# ----------------------------------------------------------------------
# FIXTURES
# ----------------------------------------------------------------------

@pytest.fixture
def config_dir(use_real_config_dir):
    """Use the actual tests/config directory."""
    return use_real_config_dir


# ----------------------------------------------------------------------
# LEGACY LOAD_CONFIG COMPAT
# ----------------------------------------------------------------------

def test_load_config_legacy_api_still_works(config_dir):
    """
    load_config() must still work and return a Config instance,
    providing backward compatibility with existing ETL-service-web usage.
    """
    cfg = load_config(profile="dev", config_dir=config_dir)
    assert isinstance(cfg, Config)
    assert cfg.get("app.profile") == "dev"


# ----------------------------------------------------------------------
# FULL MERGE: BASE + PROFILE + IMPORTS + NESTED IMPORTS
# ----------------------------------------------------------------------

def test_full_merge_dev_profile(config_dir, maybe_dump, capture_config):
    """
    application.yml
    application-dev.yml
    imports/job-default.yml
    imports/common.yml
    combined must produce correct final values.
    """
    cfg = capture_config(lambda: ConfigLoader(config_dir, profile="dev").load())
    maybe_dump(cfg)

    # Base + profile
    assert cfg.get("app.name") == "SprigTestApp"
    assert cfg.get("app.profile") == "dev"
    assert cfg.get("app.debug_mode") is True

    # Root imports
    assert cfg.get("etl.jobs.root") == "/jobs/default"
    assert cfg.get("etl.jobs.repositories.inmemory.class") == "InMemoryJobRepo"
    assert cfg.get("common.feature_flag") is True


def test_full_merge_nested_profile(config_dir):
    """
    profile=nested → imports/nested.yml + imports/misc.yml
    """
    cfg = ConfigLoader(config_dir, profile="nested").load()

    # From nested.yml
    assert cfg.get("etl.jobs.etl.jobs.foo") == "bar"

    # From misc.yml
    assert cfg.get("etl.jobs.misc.value") == 123


def test_full_merge_chain_profile(config_dir):
    """
    profile=chain → chains/chain1 → chain2 → chain3
    """
    cfg = ConfigLoader(config_dir, profile="chain").load()

    assert cfg.get("chain.level1") == "L1"
    assert cfg.get("chain.level2") == "L2"
    assert cfg.get("chain.level3") == "L3"


# ----------------------------------------------------------------------
# CIRCULAR IMPORT DETECTION
# ----------------------------------------------------------------------

def test_integration_circular_import(config_dir):
    with pytest.raises(ConfigLoadError):
        ConfigLoader(config_dir, profile="circular").load()


# ----------------------------------------------------------------------
# DOTTED KEYS ACROSS FULL MERGE
# ----------------------------------------------------------------------

def test_integration_dotted_key_access(config_dir):
    """
    Dotted-key access should always work on the fully merged tree.
    """
    cfg = ConfigLoader(config_dir, profile="dev").load()

    cls = cfg.get("etl.jobs.repositories.inmemory.class")
    flag = cfg.get("common.feature_flag")
    profile = cfg.get("app.profile")

    assert cls == "InMemoryJobRepo"
    assert flag is True
    assert profile == "dev"


# ----------------------------------------------------------------------
# ENV VAR EXPANSION
# ----------------------------------------------------------------------

def test_integration_env_var_expansion(monkeypatch, config_dir):
    monkeypatch.setenv("TEST_VALUE", "xyz123")

    cfg = ConfigLoader(config_dir, profile="envtest").load()

    assert cfg.get("env.expanded") == "xyz123"
    assert cfg.get("env.defaulted") == "fallback"


# ----------------------------------------------------------------------
# SECRET HANDLING INTEGRATION
# ----------------------------------------------------------------------

def test_integration_secrets_wrapped(config_dir):
    cfg = ConfigLoader(config_dir, profile="secrets").load()
    node = cfg.get("secrets.api_key")
    assert isinstance(node, LazySecret)


def test_integration_secret_decryption(monkeypatch, config_dir):
    """
    Integration-level test:
    - Replace secret file contents with real encrypted value.
    - Provide APP_SECRET_KEY.
    - Validate LazySecret decrypts through Config.
    """
    from cryptography.fernet import Fernet

    # Generate a real encryption key
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("APP_SECRET_KEY", key)

    f = Fernet(key.encode())
    encrypted = f.encrypt(b"hello").decode()

    # Overwrite secret file
    secrets_file = Path(config_dir) / "application-secrets.yml"
    secrets_file.write_text(
        f"secrets:\n  api_key: ENC({encrypted})\n"
    )

    cfg = ConfigLoader(config_dir, profile="secrets").load()
    assert cfg.get("secrets.api_key").get() == "hello"


# ----------------------------------------------------------------------
# APP_CONFIG_DIR DEFAULT BEHAVIOR
# ----------------------------------------------------------------------

def test_app_config_dir_env_var(monkeypatch, config_dir):
    """
    If config_dir isn’t passed, load_config() must use APP_CONFIG_DIR.
    """
    monkeypatch.setenv("APP_CONFIG_DIR", str(config_dir))

    cfg = load_config(profile="dev", config_dir=None)
    assert cfg.get("app.profile") == "dev"


# ----------------------------------------------------------------------
# SINGLETON INTEGRATION
# ----------------------------------------------------------------------

def test_integration_singleton_independent_of_loader(config_dir):
    """
    Singleton and ConfigLoader must return SEPARATE instances.
    """
    cfg1 = ConfigSingleton.get(profile="dev", config_dir=config_dir)
    cfg2 = ConfigLoader(config_dir, profile="dev").load()

    assert isinstance(cfg1, Config)
    assert isinstance(cfg2, Config)
    assert cfg1 is not cfg2


def test_integration_singleton_dotted_keys(config_dir):
    cfg = ConfigSingleton.get(profile="dev", config_dir=config_dir)
    assert cfg.get("etl.jobs.root") == "/jobs/default"


# ----------------------------------------------------------------------
# DEBUG-DUMP INTEGRATION (via capture_config fixture)
# ----------------------------------------------------------------------

@pytest.mark.usefixtures("capture_config")
def test_integration_debug_dump(request, config_dir):
    """
    Full-stack test ensuring debug-dump writes a YAML file when enabled.
    """
    dump_path = request.config.getoption("--debug-dump")
    if not dump_path:
        pytest.skip("debug dump not enabled")

    # Trigger dump
    cfg = ConfigLoader(config_dir, profile="dev").load()
    assert isinstance(cfg, Config)

    # After test, capture_config fixture should have written the file
    assert Path(dump_path).exists()
