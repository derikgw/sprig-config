"""
Full-system integration tests for SprigConfig RC3.

Validates:

- Full merge across base + profile + imports + nested imports
- load_config() backward compatibility
- Correct metadata injection under sprigconfig._meta
- Correct handling of secrets (LazySecret)
- Correct environment expansion
- Correct ConfigSingleton behavior
- Correct dotted-key access
- Correct default behavior using APP_CONFIG_DIR
- Circular import detection
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
# FIXTURE
# ----------------------------------------------------------------------

@pytest.fixture
def config_dir(use_real_config_dir):
    return use_real_config_dir


# ----------------------------------------------------------------------
# LEGACY load_config STILL WORKS
# ----------------------------------------------------------------------

def test_load_config_legacy_api_still_works(config_dir):
    cfg = load_config(profile="dev", config_dir=config_dir)
    assert isinstance(cfg, Config)

    # RC3: runtime profile stored in metadata
    assert cfg.get("sprigconfig._meta.profile") == "dev"


# ----------------------------------------------------------------------
# FULL MERGE: DEV PROFILE
# ----------------------------------------------------------------------

def test_full_merge_dev_profile(config_dir, maybe_dump, capture_config):
    cfg = capture_config(lambda: ConfigLoader(config_dir, profile="dev").load())
    maybe_dump(cfg)

    # Application values
    assert cfg.get("app.name") == "SprigTestApp"
    assert cfg.get("app.debug_mode") is True

    # Runtime profile
    assert cfg.get("sprigconfig._meta.profile") == "dev"

    # Imports
    assert cfg.get("etl.jobs.root") == "/jobs/default"
    assert cfg.get("etl.jobs.repositories.inmemory.class") == "InMemoryJobRepo"
    assert cfg.get("common.feature_flag") is True


# ----------------------------------------------------------------------
# FULL MERGE: NESTED
# ----------------------------------------------------------------------

def test_full_merge_nested_profile(config_dir):
    cfg = ConfigLoader(config_dir, profile="nested").load()

    assert cfg.get("etl.jobs.etl.jobs.foo") == "bar"
    assert cfg.get("etl.jobs.misc.value") == 123


def test_full_merge_chain_profile(config_dir):
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
# DOTTED KEY ACCESS
# ----------------------------------------------------------------------

def test_integration_dotted_key_access(config_dir):
    cfg = ConfigLoader(config_dir, profile="dev").load()

    assert cfg.get("etl.jobs.repositories.inmemory.class") == "InMemoryJobRepo"
    assert cfg.get("common.feature_flag") is True
    assert cfg.get("sprigconfig._meta.profile") == "dev"


# ----------------------------------------------------------------------
# ENV VAR EXPANSION
# ----------------------------------------------------------------------

def test_integration_env_var_expansion(monkeypatch, config_dir):
    monkeypatch.setenv("TEST_VALUE", "xyz123")

    cfg = ConfigLoader(config_dir, profile="envtest").load()

    assert cfg.get("env.expanded") == "xyz123"
    assert cfg.get("env.defaulted") == "fallback"


# ----------------------------------------------------------------------
# SECRET HANDLING
# ----------------------------------------------------------------------

def test_integration_secrets_wrapped(config_dir):
    cfg = ConfigLoader(config_dir, profile="secrets").load()
    node = cfg.get("secrets.api_key")
    assert isinstance(node, LazySecret)


def test_integration_secret_decryption(monkeypatch, config_dir):
    from cryptography.fernet import Fernet

    key = Fernet.generate_key().decode()
    monkeypatch.setenv("APP_SECRET_KEY", key)

    f = Fernet(key.encode())
    encrypted = f.encrypt(b"hello").decode()

    secrets_yml = Path(config_dir) / "application-secrets.yml"
    secrets_yml.write_text(f"secrets:\n  api_key: ENC({encrypted})\n")

    cfg = ConfigLoader(config_dir, profile="secrets").load()
    assert cfg.get("secrets.api_key").get() == "hello"


# ----------------------------------------------------------------------
# APP_CONFIG_DIR DEFAULT
# ----------------------------------------------------------------------

def test_app_config_dir_env_var(monkeypatch, config_dir):
    monkeypatch.setenv("APP_CONFIG_DIR", str(config_dir))
    cfg = load_config(profile="dev", config_dir=None)

    assert cfg.get("sprigconfig._meta.profile") == "dev"


# ----------------------------------------------------------------------
# SINGLETON
# ----------------------------------------------------------------------

def test_integration_singleton_independent_of_loader(config_dir):
    ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
    cfg1 = ConfigSingleton.get()
    cfg2 = load_config(profile="dev", config_dir=config_dir)

    assert cfg1 is not cfg2



def test_integration_singleton_dotted_keys(config_dir):
    ConfigSingleton._clear_all()
    ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
    cfg = ConfigSingleton.get()
    assert cfg.get("logging.level") == "INFO"
