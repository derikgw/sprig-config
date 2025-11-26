"""
Profile-specific behavior tests for SprigConfig RC3.

These tests exercise:

- Base application.yml loaded first
- application-<profile>.yml overlays
- Deep overriding of existing keys
- Additive merging of new keys
- Profile-specific imports
- Correct merge order: base < profile < imports
- Dotted-key access
- Correct metadata injection into sprigconfig._meta
- Runtime profile stored ONLY in sprigconfig._meta.profile
- app.profile values inside YAML preserved but never overridden by runtime profile
- Missing profile files must NOT error
"""

import pytest
from sprigconfig import (
    ConfigLoader,
    Config,
    ConfigLoadError, ConfigSingleton,
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
    application.yml sets:
        app.name = SprigTestApp
        app.profile = base

    application-dev.yml sets:
        app.profile = dev
        app.debug_mode = true

    RC3 EXPECTATIONS:

        ✔ Base keys included
        ✔ Profile overlay applied (debug_mode + profile = dev)
        ✔ YAML-derived app.profile MUST remain in the application tree
        ✔ Runtime profile MUST appear ONLY in:
              sprigconfig._meta.profile
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="dev").load()

    # --- Base + profile merge --------------------------------------------
    assert cfg.get("app.name") == "SprigTestApp"
    assert cfg.get("app.debug_mode") is True

    # YAML-defined app.profile SHOULD be overridden by application-dev.yml
    assert cfg.get("app.profile") == "dev"

    # --- Runtime profile must be stored ONLY in metadata ------------------
    assert cfg.get("sprigconfig._meta.profile") == "dev"
    assert "sprigconfig" in cfg
    assert "_meta" in cfg.get("sprigconfig")
    assert cfg.get("sprigconfig._meta.sources") is not None



def test_profile_additive_merge(config_dir):
    """
    If profile.yml contains new keys not in application.yml, they are added.
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="dev").load()

    assert "debug_mode" in cfg.get("app")
    assert cfg.get("app.debug_mode") is True


# ----------------------------------------------------------------------
# MISSING PROFILE
# ----------------------------------------------------------------------

def test_missing_profile_does_not_raise(config_dir):
    """
    If application-<missing>.yml does NOT exist,
    MUST NOT raise — a warning is okay but load must succeed.
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="does_not_exist").load()
    assert isinstance(cfg, Config)

    # runtime profile is tracked in metadata
    assert cfg.get("sprigconfig._meta.profile") == "does_not_exist"

def test_no_profile_provided_raises(config_dir):
    ConfigSingleton._clear_all()

    with pytest.raises(ConfigLoadError) as exc:
        ConfigSingleton.initialize(profile=None, config_dir=config_dir)

    assert "Profile must be provided" in str(exc.value)

# ----------------------------------------------------------------------
# PROFILE-SPECIFIC IMPORTS
# ----------------------------------------------------------------------

def test_profile_specific_import_chain(config_dir):
    """
    profile "chain" triggers chain1.yml → chain2.yml → chain3.yml
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="chain").load()

    assert cfg.get("chain.level1") == "L1"
    assert cfg.get("chain.level2") == "L2"
    assert cfg.get("chain.level3") == "L3"


def test_profile_nested_imports(config_dir):
    """
    profile "nested" triggers nested.yml + misc.yml
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="nested").load()

    assert cfg.get("etl.jobs.etl.jobs.foo") == "bar"
    assert cfg.get("etl.jobs.misc.value") == 123


# ----------------------------------------------------------------------
# PROFILE SHOULD NOT OVERRIDE ACTIVE RUNTIME PROFILE
# ----------------------------------------------------------------------

def test_profile_file_cannot_override_runtime_profile(config_dir):
    """
    YAML files may contain app.profile = base or dev,
    but runtime profile ALWAYS overrides via sprigconfig._meta.profile.
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="prod").load()

    # YAML-defined profile should remain visible
    yaml_value = cfg.get("app.profile")
    assert yaml_value in ("base", "dev", "prod", None)

    # runtime profile must appear in metadata
    assert cfg.get("sprigconfig._meta.profile") == "prod"


# ----------------------------------------------------------------------
# PROFILE + IMPORT MERGE ORDER
# ----------------------------------------------------------------------

def test_profile_then_import_order(config_dir):
    """
    Expected merge order:
        1. application.yml
        2. application-<profile>.yml
        3. imports from application.yml
        4. imports from profile.yml (if any)
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="dev").load()

    # base+profile
    assert cfg.get("app.debug_mode") is True

    # imports after profile
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
    Dotted access works across merged values.
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="dev").load()

    assert cfg.get("etl.jobs.repositories.inmemory.class") == "InMemoryJobRepo"
    assert cfg.get("common.feature_flag") is True

    # runtime profile stored only in metadata
    assert cfg.get("sprigconfig._meta.profile") == "dev"
