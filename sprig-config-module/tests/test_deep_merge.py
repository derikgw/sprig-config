# tests/test_deep_merge.py
"""
Deep merge tests for the future SprigConfig architecture.

These tests define the EXACT deep merge behavior SprigConfig must follow:

    - Deep, recursive merging between base → profile → imports.
    - Order preservation: base first, profile second, then imports in sequence.
    - No structural "correction": imported trees appear exactly where placed.
    - Nested imports build nested trees.
    - Misaligned structures are merged into place as-is.
    - Lists overwrite, not append.
    - Circular imports raise ConfigLoadError.
    - Dotted-key access resolves merged values.
    - Merge warnings suppressed if suppress_config_merge_warnings=true.

These tests WILL FAIL until ConfigLoader + deep merge logic is implemented.
"""

import pytest
from sprigconfig import (
    ConfigLoader,
    Config,
    ConfigLoadError,
)


# ----------------------------------------------------------------------
# FIXTURE FOR REAL CONFIG DIR
# ----------------------------------------------------------------------

@pytest.fixture
def config_dir(use_real_config_dir):
    return use_real_config_dir


# ----------------------------------------------------------------------
# BASIC DEEP MERGE
# ----------------------------------------------------------------------

def test_deep_merge_root_imports(config_dir, capture_config):
    """
    application.yml imports:
        - imports/job-default.yml
        - imports/common.yml

    Must merge deeply with priority:
        base < dev < imported in listed order
    """
    cfg = capture_config(lambda: ConfigLoader(config_dir, profile="dev").load())

    # from job-default.yml
    assert cfg.get("etl.jobs.root") == "/jobs/default"
    assert cfg.get("etl.jobs.default_shell") == "/bin/bash"

    # from common.yml
    assert cfg.get("common.feature_flag") is True

    # from dev profile
    assert cfg.get("app.debug_mode") is True


def test_deep_merge_profile_override(config_dir):
    """
    Profile overrides base fields deeply.
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="dev").load()

    assert cfg.get("app.name") == "SprigTestApp"
    assert cfg.get("app.debug_mode") is True  # profile override


# ----------------------------------------------------------------------
# MISALIGNED STRUCTURES
# ----------------------------------------------------------------------

def test_misaligned_import_structure_kept_as_is(config_dir):
    """
    application-nested.yml places imports under a nested key.
    The imported yaml defines unrelated root keys.

    Expected:
        nested location must receive that structure as-is.
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="nested").load()

    # misc.yml is imported under etl.jobs
    assert cfg.get("etl.jobs.misc.value") == 123


# ----------------------------------------------------------------------
# NESTED IMPORT BEHAVIOR
# ----------------------------------------------------------------------

def test_nested_import_creates_nested_trees(config_dir):
    """
    If a file imports a YAML containing its own etl.jobs subtree,
    the merge must nest it under the parent node exactly.

    For nested.yml:
        etl.jobs.foo = bar
    Expected location:
        cfg["etl"]["jobs"]["etl"]["jobs"]["foo"] == "bar"
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="nested").load()
    assert cfg.get("etl.jobs.etl.jobs.foo") == "bar"


# ----------------------------------------------------------------------
# LIST MERGE BEHAVIOR
# ----------------------------------------------------------------------

def test_lists_overwrite_not_append(config_dir):
    """
    application-list.yml imports a file that defines a list.
    Imported list must replace prior list.
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="list").load()
    assert cfg.get("features.enabled") == ["three"]


# ----------------------------------------------------------------------
# IMPORT CHAIN BEHAVIOR
# ----------------------------------------------------------------------

def test_recursive_import_chain(config_dir):
    """
    chain1.yml → chain2.yml → chain3.yml
    Each imports the next.

    Merge order:
      base < profile < chain1 < chain2 < chain3
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="chain").load()

    assert cfg.get("chain.level1") == "L1"
    assert cfg.get("chain.level2") == "L2"
    assert cfg.get("chain.level3") == "L3"


# ----------------------------------------------------------------------
# CIRCULAR IMPORT DETECTION
# ----------------------------------------------------------------------

def test_circular_import_detection(config_dir):
    """
    application-circular.yml imports a → b → a...
    Must raise ConfigLoadError.
    """
    with pytest.raises(ConfigLoadError):
        ConfigLoader(config_dir=config_dir, profile="circular").load()


# ----------------------------------------------------------------------
# DOTTED-KEY ACCESS POST MERGE
# ----------------------------------------------------------------------

def test_dotted_key_access_after_merge(config_dir):
    """
    The merged config must support dotted-key lookups.
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="dev").load()

    cls = cfg.get("etl.jobs.repositories.inmemory.class")
    params = cfg.get("etl.jobs.repositories.inmemory.params.x")

    assert cls == "InMemoryJobRepo"
    assert params == 1


# ----------------------------------------------------------------------
# MERGE SUPPRESSION FLAG
# ----------------------------------------------------------------------

def test_merge_warning_suppression_flag(config_dir):
    """
    If suppress_config_merge_warnings = true,
    no warnings should be emitted during deep merge.

    NOTE: Actual logging assertion (capture) is not performed here,
    but we assert the flag survives the load pipeline.
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="suppress").load()

    assert cfg.get("suppress_config_merge_warnings") is True


# ----------------------------------------------------------------------
# MULTI-LAYER IMPORT + PROFILE OVERRIDE
# ----------------------------------------------------------------------

def test_merge_profile_import_interplay(config_dir):
    """
    Tests that:
      - base defines values
      - profile overrides some of them
      - imports fill new structure
      - final structure reflects correct precedence
    """
    cfg = ConfigLoader(config_dir=config_dir, profile="dev").load()

    # from base.yml
    assert cfg.get("app.name") == "SprigTestApp"

    # from profile.yml
    assert cfg.get("app.debug_mode") is True

    # from imported job-default.yml
    assert cfg.get("etl.jobs.root") == "/jobs/default"


# ----------------------------------------------------------------------
# RAW DICT MERGES (BACKWARD COMPAT)
# ----------------------------------------------------------------------

def test_deep_merge_function_still_supports_dicts(config_dir):
    """
    SprigConfig.deep_merge must continue to support raw dict → dict merges
    for backward compatibility.
    """
    from sprigconfig import deep_merge

    base = {
        "a": {"b": 1},
        "x": 5
    }
    override = {
        "a": {"c": 2},
        "x": 7
    }

    result = deep_merge(base, override)
    assert result == {"a": {"b": 1, "c": 2}, "x": 7}
