from dataclasses import dataclass
from pathlib import Path

import pytest

from sprigconfig import ConfigLoader
from sprigconfig.exceptions import ConfigValidationError


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
