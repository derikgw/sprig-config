from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from sprigconfig import ConfigLoader, load_config
from sprigconfig.exceptions import ConfigValidationError
import sprigconfig.config_loader as config_loader_module


def _write_yaml(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


@dataclass
class DatabaseSchema:
    host: str
    port: int


@dataclass
class AppSectionSchema:
    name: str
    debug_mode: bool


@dataclass
class RootSchema:
    app: AppSectionSchema
    database: DatabaseSchema


def test_schema_validation_success(tmp_path):
    _write_yaml(
        tmp_path / "application.yml",
        """
app:
  name: TestApp
  debug_mode: true
database:
  host: localhost
  port: 5432
""",
    )

    cfg = ConfigLoader(config_dir=tmp_path, profile="dev", schema=RootSchema).load()
    assert cfg.get("app.name") == "TestApp"
    assert cfg.get("database.port") == 5432


def test_schema_validation_missing_required_field(tmp_path):
    _write_yaml(
        tmp_path / "application.yml",
        """
app:
  name: TestApp
database:
  host: localhost
  port: 5432
""",
    )

    with pytest.raises(ConfigValidationError) as exc:
        ConfigLoader(config_dir=tmp_path, profile="dev", schema=RootSchema).load()

    assert "Missing required key 'app.debug_mode'" in str(exc.value)


def test_schema_validation_type_mismatch(tmp_path):
    _write_yaml(
        tmp_path / "application.yml",
        """
app:
  name: TestApp
  debug_mode: "not-bool"
database:
  host: localhost
  port: 5432
""",
    )

    with pytest.raises(ConfigValidationError) as exc:
        ConfigLoader(config_dir=tmp_path, profile="dev", schema=RootSchema).load()

    assert "Type mismatch at 'app.debug_mode'" in str(exc.value)


def test_schema_validation_unknown_key_rejected(tmp_path):
    _write_yaml(
        tmp_path / "application.yml",
        """
app:
  name: TestApp
  debug_mode: true
database:
  host: localhost
  port: 5432
  driver: postgresql
""",
    )

    with pytest.raises(ConfigValidationError) as exc:
        ConfigLoader(config_dir=tmp_path, profile="dev", schema=RootSchema).load()

    assert "Unknown key 'database.driver'" in str(exc.value)


def test_schema_validation_nested_type_path(tmp_path):
    _write_yaml(
        tmp_path / "application.yml",
        """
app:
  name: TestApp
  debug_mode: true
database:
  host: localhost
  port: not-a-number
""",
    )

    with pytest.raises(ConfigValidationError) as exc:
        ConfigLoader(config_dir=tmp_path, profile="dev", schema=RootSchema).load()

    assert "Type mismatch at 'database.port'" in str(exc.value)


def test_existing_apps_remain_unrestricted_without_schema(tmp_path):
    """Legacy callers must not acquire validation constraints by upgrading."""
    _write_yaml(
        tmp_path / "application.yml",
        """
arbitrary:
  keys:
    added_by_an_old_app: true
mixed_values:
  - 1
  - text
  - nested: value
""",
    )

    cfg = ConfigLoader(config_dir=tmp_path, profile="dev").load()

    assert cfg.get("arbitrary.keys.added_by_an_old_app") is True
    assert cfg.get("mixed_values")[2].get("nested") == "value"
    assert cfg.get("app.profile") == "dev"
    assert cfg.get("sprigconfig._meta.profile") == "dev"


def test_legacy_path_never_invokes_validator(tmp_path, monkeypatch):
    _write_yaml(tmp_path / "application.yml", "legacy: untouched\n")

    def fail_if_called(config, schema):
        raise AssertionError("validator must remain opt-in")

    monkeypatch.setattr(config_loader_module, "validate_schema", fail_if_called)

    cfg = ConfigLoader(config_dir=tmp_path, profile="dev").load()

    assert cfg.get("legacy") == "untouched"


@dataclass
class LegacyTypeSchema:
    retries: int


def test_legacy_load_ignores_code_type_mismatch_without_schema(tmp_path):
    """A code-side schema has no effect unless the caller explicitly opts in."""
    _write_yaml(tmp_path / "application.yml", 'retries: "not-an-integer"\n')

    cfg = ConfigLoader(config_dir=tmp_path, profile="dev").load()

    assert cfg.get("retries") == "not-an-integer"


def test_legacy_load_config_signature_still_works_without_schema(tmp_path):
    _write_yaml(tmp_path / "application.yml", "legacy: still-works\n")

    cfg = load_config(profile="dev", config_dir=tmp_path)

    assert cfg.get("legacy") == "still-works"


def test_load_config_convenience_api_accepts_schema(tmp_path):
    _write_yaml(
        tmp_path / "application.yml",
        """
app:
  name: TestApp
  debug_mode: true
database:
  host: localhost
  port: 5432
""",
    )

    cfg = load_config(profile="dev", config_dir=tmp_path, schema=RootSchema)

    assert cfg.get("database.host") == "localhost"


@dataclass
class FlexibleSchema:
    required: str
    optional: int | None = None
    labels: list[str] = field(default_factory=list)
    attributes: dict[str, int] = field(default_factory=dict)
    unrestricted: Any = None


def test_defaults_optionals_and_typed_collections(tmp_path):
    _write_yaml(
        tmp_path / "application.yml",
        """
required: present
optional: null
labels: [one, two]
attributes:
  retries: 3
unrestricted:
  old_app_shape: [anything, 42]
""",
    )

    cfg = ConfigLoader(config_dir=tmp_path, profile="dev", schema=FlexibleSchema).load()

    assert cfg.get("optional") is None
    assert cfg.get("labels") == ["one", "two"]
    assert cfg.get("attributes.retries") == 3


def test_defaulted_schema_fields_may_be_absent(tmp_path):
    _write_yaml(tmp_path / "application.yml", "required: present\n")

    cfg = ConfigLoader(config_dir=tmp_path, profile="dev", schema=FlexibleSchema).load()

    assert cfg.get("required") == "present"
    assert "optional" not in cfg


@dataclass
class ImportedSchema:
    shared: dict[str, str]
    service: dict[str, int | str]


def test_validation_runs_after_import_and_profile_merges(tmp_path):
    _write_yaml(
        tmp_path / "application.yml",
        """
imports: [imports/common]
service:
  name: api
  workers: 1
""",
    )
    (tmp_path / "imports").mkdir()
    _write_yaml(tmp_path / "imports" / "common.yml", "shared:\n  region: us-east\n")
    _write_yaml(tmp_path / "application-prod.yml", "service:\n  workers: 4\n")

    # Imports are control syntax and are removed before schema validation.
    cfg = ConfigLoader(config_dir=tmp_path, profile="prod", schema=ImportedSchema).load()

    assert cfg.get("shared.region") == "us-east"
    assert cfg.get("service.workers") == 4


@dataclass
class MinimalSchema:
    value: str


def test_runtime_generated_sections_do_not_have_to_be_in_schema(tmp_path):
    _write_yaml(tmp_path / "application.yml", "value: accepted\n")

    cfg = ConfigLoader(config_dir=tmp_path, profile="dev", schema=MinimalSchema).load()

    assert cfg.get("app.profile") == "dev"
    assert cfg.get("sprigconfig._meta.profile") == "dev"


@pytest.mark.parametrize(
    ("config_format", "filename", "content"),
    [
        ("yaml", "application.yml", "value: accepted\n"),
        ("json", "application.json", '{"value": "accepted"}'),
        ("toml", "application.toml", 'value = "accepted"'),
    ],
)
def test_schema_validation_is_format_agnostic(
    tmp_path, config_format, filename, content
):
    _write_yaml(tmp_path / filename, content)

    cfg = ConfigLoader(
        config_dir=tmp_path,
        profile="dev",
        config_format=config_format,
        schema=MinimalSchema,
    ).load()

    assert cfg.get("value") == "accepted"


def test_schema_must_be_a_dataclass_type(tmp_path):
    _write_yaml(tmp_path / "application.yml", "value: accepted\n")

    with pytest.raises(ConfigValidationError, match="Schema must be a dataclass type"):
        ConfigLoader(config_dir=tmp_path, profile="dev", schema=dict).load()


def test_dataclass_instance_is_rejected_as_schema(tmp_path):
    _write_yaml(tmp_path / "application.yml", "value: accepted\n")

    with pytest.raises(ConfigValidationError, match="Schema must be a dataclass type"):
        ConfigLoader(
            config_dir=tmp_path,
            profile="dev",
            schema=MinimalSchema("accepted"),
        ).load()
