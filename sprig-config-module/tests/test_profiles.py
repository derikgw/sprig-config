# tests/test_profiles.py
"""
Profile-specific behavior tests for the new SprigConfig architecture.

These tests exercise:

- application.yml → application-<profile>.yml precedence
- deep overriding of existing keys
- additive merging of new keys
- profile-specific imports
- profile overlay order: base < profile < imports
- dotted-key access to merged profile values
- ignoring `app.profile` values inside files (explicit active profile wins)
- missing profile file should NOT error
- merge suppression flag loaded via profile

All tests WILL FAIL until ConfigLoader, Config, and deep-merge logic
are implemented per the new design.
"""

import os
import pytest
from sprigconfig import (
    ConfigLoader,
    Config,
    ConfigLoadError,
)


# ----------------------------------------------------------------------
# FIXTURE
# ----------------------------------------------------------------------

@pytest.fixture
def config_dir(use_real_config_dir):
    """Use real tests/config directory."""
    return use_real_config_dir


# ----------------------------------------------------------------------
# BASE + PROFILE MERGE
# ----------------------------------------------------------------------

def test_profile_overrides_base_values(config_dir):
    """
    application.yml sets app.profile = base, app.name = SprigTestApp
    application-dev.yml overrides:
        app.profile = dev
        app.debug_mode = true

    EXPECTED:
        - base keys included
        - profile overrides applied
        - dotted access works
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="dev").load()

    assert cfg.get("app.name") == "SprigTestApp"
    assert cfg.get("app.profile") == "dev"
    assert cfg.get("app.debug_mode") is True


def test_profile_additive_merge(config_dir):
    """
    If profile contains new keys not in application.yml, they are added.
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="dev").load()

    assert "debug_mode" in cfg.get("app")
    assert cfg.get("app.debug_mode") is True


# ----------------------------------------------------------------------
# MISSING PROFILE
# ----------------------------------------------------------------------

def test_missing_profile_does_not_raise(config_dir):
    """
    If application-nonexistent.yml does not exist,
    MUST NOT raise — a warning is okay, but loader should succeed.
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="does_not_exist").load()
    assert isinstance(cfg, Config)
    assert cfg.get("app.profile") == "does_not_exist"


# ----------------------------------------------------------------------
# PROFILE-SPECIFIC IMPORTS
# ----------------------------------------------------------------------

def test_profile_specific_import_chain(config_dir):
    """
    profile "chain" triggers a chain of imports:
        chain1.yml → chain2.yml → chain3.yml
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="chain").load()

    assert cfg.get("chain.level1") == "L1"
    assert cfg.get("chain.level2") == "L2"
    assert cfg.get("chain.level3") == "L3"


def test_profile_nested_imports(config_dir):
    """
    profile "nested" triggers nested imports:
        - nested.yml
        - misc.yml
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="nested").load()

    # From nested.yml
    assert cfg.get("etl.jobs.etl.jobs.foo") == "bar"
    # From misc.yml
    assert cfg.get("etl.jobs.misc.value") == 123


# ----------------------------------------------------------------------
# PROFILE SHOULD NOT OVERRIDE ACTIVE PROFILE
# ----------------------------------------------------------------------

def test_profile_file_cannot_override_runtime_profile(config_dir):
    """
    application.yml sets:
        app.profile = base

    application-dev.yml sets:
        app.profile = dev

    If profile="prod" is requested:
        cfg.app.profile MUST be "prod", not "dev" or "base".
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="prod").load()

    assert cfg.get("app.profile") == "prod"


# ----------------------------------------------------------------------
# PROFILE + IMPORT MERGE ORDER
# ----------------------------------------------------------------------

def test_profile_then_import_order(config_dir):
    """
    Expected merge order:
        1. application.yml
        2. application-dev.yml
        3. imports from application.yml
        4. imports from profile (if any)
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="dev").load()

    # Base & profile merged
    assert cfg.get("app.debug_mode") is True

    # Imports applied after profile
    assert cfg.get("common.feature_flag") is True
    assert cfg.get("etl.jobs.root") == "/jobs/default"


# ----------------------------------------------------------------------
# SUPPRESS MERGE WARNINGS VIA PROFILE
# ----------------------------------------------------------------------

def test_profile_merge_suppression_flag(config_dir):
    """
    application-suppress.yml contains:
        suppress_config_merge_warnings: true
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="suppress").load()

    assert cfg.get("suppress_config_merge_warnings") is True


# ----------------------------------------------------------------------
# DOTTED-KEY ACCESS FOR PROFILE VALUES
# ----------------------------------------------------------------------

def test_profile_dotted_key_access(config_dir):
    """
    After merge, dotted key access must work across base+profile+imports.
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="dev").load()

    assert cfg.get("etl.jobs.repositories.inmemory.class") == "InMemoryJobRepo"
    assert cfg.get("common.feature_flag") is True
    assert cfg.get("app.profile") == "dev"
