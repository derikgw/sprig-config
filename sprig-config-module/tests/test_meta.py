# tests/test_meta.py
"""
Tests for SprigConfig runtime metadata injection.

These tests define the behavior of the automatically-added:

    sprigconfig._meta.profile

The metadata:

    • MUST always exist after ConfigLoader.load()
    • MUST contain the runtime profile (string passed into load_config or ConfigLoader)
    • MUST NOT overwrite any user-defined config keys
    • MUST NOT modify application or profile YAML trees
    • MUST be separate from user config
"""

import pytest
from sprigconfig import ConfigLoader, Config


# ----------------------------------------------------------------------
# FIXTURE
# ----------------------------------------------------------------------

@pytest.fixture
def config_dir(use_real_config_dir):
    """Use the tests/config directory."""
    return use_real_config_dir


# ----------------------------------------------------------------------
# BASIC PROFILE METADATA
# ----------------------------------------------------------------------

def test_meta_injects_runtime_profile(config_dir):
    """
    The runtime profile MUST be injected into:

        sprigconfig._meta.profile

    regardless of what appears in YAML files.
    """
    cfg = ConfigLoader(config_dir, profile="dev").load()

    assert cfg.get("sprigconfig._meta.profile") == "dev"


def test_meta_profile_always_present_even_if_missing_profile_file(config_dir):
    """
    If application-<profile>.yml does NOT exist, loader succeeds AND metadata still records
    the runtime profile.
    """
    cfg = ConfigLoader(config_dir, profile="does_not_exist").load()

    assert cfg.get("sprigconfig._meta.profile") == "does_not_exist"


# ----------------------------------------------------------------------
# MUST NOT ALTER USER CONFIG TREES
# ----------------------------------------------------------------------

def test_meta_does_not_modify_application_tree(config_dir):
    """
    sprigconfig._meta.profile MUST NOT modify or replace any user config tree.

    Example:
        application.yml defines app.profile = base
        application-dev.yml defines app.profile = dev

    When profile="dev", deep merge still overrides YAML app.profile to "dev".
    But sprigconfig._meta.profile must exist separately.
    """
    cfg = ConfigLoader(config_dir, profile="dev").load()

    # YAML merge result
    assert cfg.get("app.profile") == "dev"

    # Metadata
    assert cfg.get("sprigconfig._meta.profile") == "dev"


def test_meta_cannot_override_user_keys(config_dir):
    """
    If the user defines a key: sprigconfig: _meta: profile inside YAML
    (unlikely but valid YAML), SprigConfig must NOT overwrite that.
    """
    # Pretend user intentionally created this file:
    # tests/config/application-user-meta.yml
    # with contents:
    #   sprigconfig:
    #     _meta:
    #       profile: should_not_be_overwritten
    #
    # The loader must not erase it.

    cfg = ConfigLoader(config_dir, profile="user-meta").load()

    assert cfg.get("sprigconfig._meta.profile") == "should_not_be_overwritten"


# ----------------------------------------------------------------------
# TYPE SAFETY
# ----------------------------------------------------------------------

def test_meta_profile_is_string(config_dir):
    cfg = ConfigLoader(config_dir, profile="dev").load()
    val = cfg.get("sprigconfig._meta.profile")

    assert isinstance(val, str)
    assert val == "dev"
