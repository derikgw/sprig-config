# tests/test_config.py
"""
Tests for the future Config class.

These tests define the expected behavior for the new Config object that
will be returned by ConfigLoader and load_config().

Config must:

- Behave like an immutable or read-only Mapping for consumers.
- Wrap nested dicts automatically so cfg["a"]["b"] is also a Config.
- Support dotted-key lookup via cfg.get("a.b.c").
- Support shallow get via cfg.get("key", default).
- Provide a to_dict() method that emits raw Python dicts.
- Provide a dump(path, safe=True) method for writing YAML.
- Redact LazySecret values unless explicitly asked not to.
- Remain backward compatible with dict readers.

These tests WILL FAIL until Config is implemented.
"""

import pytest
import yaml
from sprigconfig import ConfigLoadError
from sprigconfig import (
    Config,           # future implementation under test
)
from sprigconfig.lazy_secret import LazySecret


# ----------------------------------------------------------------------
# BASIC CONSTRUCTION
# ----------------------------------------------------------------------

def test_config_wraps_dicts_recursively():
    """
    Config(data) should wrap all nested dicts as Config automatically.
    """
    data = {"a": {"b": {"c": 1}}, "x": 5}
    cfg = Config(data)

    assert isinstance(cfg, Config)
    assert isinstance(cfg["a"], Config)
    assert isinstance(cfg["a"]["b"], Config)
    assert cfg["a"]["b"]["c"] == 1
    assert cfg["x"] == 5


def test_config_is_mapping_like():
    """
    Config should behave like a Mapping:
    - keys()
    - items()
    - iteration
    - __contains__
    """
    cfg = Config({"a": 1, "b": 2})

    assert set(cfg.keys()) == {"a", "b"}
    assert set(cfg.items()) == {("a", 1), ("b", 2)}
    assert "a" in cfg
    assert list(iter(cfg)) == ["a", "b"] or ["b", "a"]


# ----------------------------------------------------------------------
# DOTTED-KEY ACCESS
# ----------------------------------------------------------------------

def test_dotted_key_access():
    cfg = Config({"etl": {"jobs": {"root": "/jobs"}}})

    assert cfg.get("etl.jobs.root") == "/jobs"
    assert cfg.get("etl.jobs") == {"root": "/jobs"} or isinstance(cfg.get("etl.jobs"), Config)


def test_dotted_key_missing_returns_default():
    cfg = Config({"a": {"b": 1}})

    assert cfg.get("a.b.c", default="missing") == "missing"
    assert cfg.get("does.not.exist") is None


def test_dotted_key_nesting_does_not_modify_data():
    """
    Calling get("a.b.c") should NOT alter the underlying stored dict.
    """
    data = {"a": {"b": {"c": 1}}}
    cfg = Config(data)

    _ = cfg.get("a.b.c")
    assert data == {"a": {"b": {"c": 1}}}


# ----------------------------------------------------------------------
# NESTED ACCESS
# ----------------------------------------------------------------------

def test_nested_access_returns_config():
    cfg = Config({"a": {"b": {"c": 42}}})

    assert isinstance(cfg["a"], Config)
    assert isinstance(cfg["a"]["b"], Config)
    assert cfg["a"]["b"]["c"] == 42


def test_nested_missing_key_raises_keyerror():
    cfg = Config({"a": {"b": 1}})

    with pytest.raises(KeyError):
        _ = cfg["a"]["c"]


# ----------------------------------------------------------------------
# TO_DICT BEHAVIOR
# ----------------------------------------------------------------------

def test_to_dict_returns_plain_dict():
    data = {"a": {"b": {"c": 1}}, "x": 5}
    cfg = Config(data)

    result = cfg.to_dict()
    assert isinstance(result, dict)
    assert result == data
    assert result is not data  # must be a deep copy


def test_to_dict_recursively_converts_nested_config():
    cfg = Config({"a": Config({"b": 1})})

    d = cfg.to_dict()
    assert d == {"a": {"b": 1}}


# ----------------------------------------------------------------------
# DUMP (SAFE)
# ----------------------------------------------------------------------

def test_config_dump_writes_yaml(tmp_path):
    cfg = Config({"a": 1, "b": {"c": 2}})
    out = tmp_path / "out.yml"

    cfg.dump(out)
    written = yaml.safe_load(out.read_text())

    assert written == {"a": 1, "b": {"c": 2}}


# ----------------------------------------------------------------------
# SECRET HANDLING
# ----------------------------------------------------------------------

def test_config_to_dict_redacts_lazysecret():
    cfg = Config({
        "secret": LazySecret("ENC(xxx)", key=None)
    })

    d = cfg.to_dict()
    assert d["secret"] == "<LazySecret>"


def test_config_dump_redacts_lazysecret(tmp_path):
    cfg = Config({
        "secret": LazySecret("ENC(xxx)", key=None)
    })
    out = tmp_path / "out.yml"

    cfg.dump(out, safe=True)
    written = yaml.safe_load(out.read_text())
    assert written["secret"] == "<LazySecret>"


def test_config_dump_can_output_plaintext_secrets(tmp_path, monkeypatch):
    secret = LazySecret("ENC(xxx)", key="dummy")

    # Monkeypatch get() at the class level
    monkeypatch.setattr(LazySecret, "get", lambda self: "plaintext")

    cfg = Config({"secret": secret})
    out = tmp_path / "x.yml"
    cfg.dump(out, safe=False)

    txt = out.read_text()
    assert "plaintext" in txt


def test_config_dump_raises_if_cannot_reveal_secret(tmp_path):
    secret = LazySecret("ENC(xxx)", key=None)  # cannot decrypt
    cfg = Config({"secret": secret})

    with pytest.raises(ConfigLoadError):
        cfg.dump(tmp_path / "out.yml", safe=False)
