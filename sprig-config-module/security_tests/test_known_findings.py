"""Executable issue #41 cases, not assertions that these paths are secure.

Strict xfails keep known defects visible and detect when fixes require removing
the annotation. SECURITY_ENFORCE_KNOWN=1 makes every case a normal failing test.
"""
import os
import traceback

import pytest
from cryptography.fernet import Fernet

from sprigconfig import Config, ConfigLoader, ConfigLoadError, ConfigSingleton, ConfigValue
from sprigconfig.lazy_secret import LazySecret


known = pytest.mark.xfail(
    condition=os.environ.get("SECURITY_ENFORCE_KNOWN") != "1",
    strict=True,
    raises=AssertionError,
    reason="Known hardening gap tracked in https://github.com/derikgw/sprig-config/issues/41",
)
MARKER = "SYNTHETIC_SECURITY_MARKER"


@known
def test_yaml_errors_do_not_disclose_expanded_values(tmp_path, monkeypatch):
    monkeypatch.setenv("SPRIG_SECURITY_TEST_VALUE", MARKER + '"broken')
    (tmp_path / "application.yaml").write_text('password: "${SPRIG_SECURITY_TEST_VALUE}"\n')
    with pytest.raises(ConfigLoadError) as error:
        ConfigLoader(tmp_path, "test").load()
    assert MARKER not in "".join(traceback.format_exception(error.value))


@known
def test_decrypted_binding_errors_do_not_disclose_values(monkeypatch):
    key = Fernet.generate_key()
    token = Fernet(key).encrypt(MARKER.encode()).decode()
    cfg = Config({"secret": LazySecret(token, key=key)})
    monkeypatch.setattr(ConfigSingleton, "_instance", cfg)

    class Binding:
        value: int = ConfigValue("secret", decrypt=True)

    with pytest.raises(ConfigLoadError) as error:
        _ = Binding().value
    assert MARKER not in "".join(traceback.format_exception(error.value))


@known
def test_scalar_substitution_cannot_inject_configuration(tmp_path, monkeypatch):
    monkeypatch.setenv("SPRIG_SECURITY_TEST_VALUE", "demo\nsecurity:\n  enabled: false")
    (tmp_path / "application.yaml").write_text("label: ${SPRIG_SECURITY_TEST_VALUE}\n")
    cfg = ConfigLoader(tmp_path, "test").load()
    assert "security" not in cfg


@known
def test_profile_selection_cannot_escape_directory(tmp_path):
    base = tmp_path / "config"
    base.mkdir()
    (base / "application.yaml").write_text("synthetic: true\n")
    (base / "application-dev").mkdir()
    (tmp_path / "outside.yaml").write_text("outside_loaded: true\n")
    try:
        cfg = ConfigLoader(base, "dev/../../outside").load()
    except ConfigLoadError:
        return  # Rejection at validation or containment is acceptable.
    assert not cfg.get("outside_loaded", False)


@known
def test_root_symlink_cannot_escape_directory(tmp_path):
    base = tmp_path / "config"
    base.mkdir()
    outside = tmp_path / "outside.yaml"
    outside.write_text("outside_loaded: true\n")
    (base / "application.yaml").symlink_to(outside)
    try:
        cfg = ConfigLoader(base, "test").load()
    except ConfigLoadError:
        return
    assert not cfg.get("outside_loaded", False)
