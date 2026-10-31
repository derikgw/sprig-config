"""Executable issue #41 cases and regression checks for resolved findings.

Open findings remain strict xfails; resolved findings run as normal regression
tests. SECURITY_ENFORCE_KNOWN=1 makes every remaining case a normal test.
"""
import os
import subprocess
import sys
import traceback

import pytest
from cryptography.fernet import Fernet
from sprigconfig.parsers import JsonParser

from sprigconfig import (
    Config,
    ConfigLoader,
    ConfigLoadError,
    ConfigSingleton,
    ConfigValue,
    ConfigurationProperties,
    instantiate,
)
from sprigconfig.lazy_secret import LazySecret


known = pytest.mark.xfail(
    condition=os.environ.get("SECURITY_ENFORCE_KNOWN") != "1",
    strict=True,
    raises=AssertionError,
    reason="Known hardening gap tracked in https://github.com/derikgw/sprig-config/issues/41",
)
MARKER = "SYNTHETIC_SECURITY_MARKER"


def test_yaml_errors_do_not_disclose_expanded_values(tmp_path, monkeypatch):
    monkeypatch.setenv("SPRIG_SECURITY_TEST_VALUE", MARKER + '"broken')
    (tmp_path / "application.yaml").write_text('password: "${SPRIG_SECURITY_TEST_VALUE}"\n')
    with pytest.raises(ConfigLoadError) as error:
        ConfigLoader(tmp_path, "test").load()
    formatted = "".join(traceback.format_exception(error.value))
    assert MARKER not in str(error.value)
    assert MARKER not in formatted
    assert "line 1" in str(error.value)
    assert "column" in str(error.value)


def test_cli_parse_errors_do_not_disclose_expanded_values(tmp_path, monkeypatch):
    monkeypatch.setenv("SPRIG_SECURITY_TEST_VALUE", MARKER + '"broken')
    (tmp_path / "application.yml").write_text(
        'password: "${SPRIG_SECURITY_TEST_VALUE}"\n'
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "sprigconfig.cli",
            "dump",
            "--config-dir",
            str(tmp_path),
            "--profile",
            "dev",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert MARKER not in result.stdout
    assert MARKER not in result.stderr
    assert "line 1" in result.stderr
    assert "column" in result.stderr


def test_json_parser_errors_do_not_disclose_source_text():
    with pytest.raises(ValueError) as error:
        JsonParser().parse(f'{{"password": "{MARKER}" invalid}}')
    assert MARKER not in str(error.value)
    assert "line 1" in str(error.value)
    assert "column" in str(error.value)


def test_toml_errors_do_not_disclose_source_text(tmp_path):
    (tmp_path / "application.toml").write_text(f'value = "{MARKER}" invalid\n')
    with pytest.raises(ConfigLoadError) as error:
        ConfigLoader(tmp_path, "test", config_format="toml").load()
    assert MARKER not in str(error.value)
    assert "line 1" in str(error.value)
    assert "column" in str(error.value)


def test_decrypted_binding_errors_do_not_disclose_values(monkeypatch):
    key = Fernet.generate_key()
    token = Fernet(key).encrypt(MARKER.encode()).decode()
    cfg = Config({"secret": LazySecret(token, key=key)})
    monkeypatch.setattr(ConfigSingleton, "_instance", cfg)

    class Binding:
        value: int = ConfigValue("secret", decrypt=True)

    with pytest.raises(ConfigLoadError) as error:
        _ = Binding().value
    formatted = "".join(traceback.format_exception(error.value))
    assert MARKER not in str(error.value)
    assert MARKER not in formatted
    assert "secret" in str(error.value)
    assert "int" in str(error.value)


def test_configuration_properties_errors_do_not_disclose_values(monkeypatch):
    monkeypatch.setattr(
        ConfigSingleton,
        "_instance",
        Config({"section": {"value": MARKER}}),
    )

    @ConfigurationProperties(prefix="section")
    class Binding:
        value: int

    with pytest.raises(ConfigLoadError) as error:
        Binding()
    formatted = "".join(traceback.format_exception(error.value))
    assert MARKER not in str(error.value)
    assert MARKER not in formatted
    assert "Binding.value" in str(error.value)
    assert "int" in str(error.value)


def test_instantiate_conversion_errors_do_not_disclose_values():
    with pytest.raises(ConfigLoadError) as error:
        instantiate({
            "_target_": "tests.test_instantiate.SimpleAdapter",
            "url": "postgres://localhost",
            "port": MARKER,
        })
    formatted = "".join(traceback.format_exception(error.value))
    assert MARKER not in str(error.value)
    assert MARKER not in formatted
    assert "port" in str(error.value)
    assert "int" in str(error.value)


def test_instantiate_constructor_errors_do_not_disclose_values():
    with pytest.raises(ConfigLoadError) as error:
        instantiate({
            "_target_": "tests.test_instantiate.LeakingConstructor",
            "password": MARKER,
        })
    formatted = "".join(traceback.format_exception(error.value))
    assert MARKER not in str(error.value)
    assert MARKER not in formatted
    assert "LeakingConstructor" in str(error.value)


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
