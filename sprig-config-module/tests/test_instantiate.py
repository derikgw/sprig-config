"""
Tests for _target_ dynamic class instantiation.

Tests cover:
- Instantiation from real config files (YAML, JSON, TOML formats)
- Type conversion during instantiation
- Integration with @config_inject decorator
- Recursive instantiation of nested _target_ objects
- Error handling and validation

All tests use actual config files in tests/config/ to verify format-agnostic behavior.
"""

import pytest
from pathlib import Path

from sprigconfig import ConfigSingleton, instantiate
from sprigconfig.config_loader import ConfigLoader
from sprigconfig.exceptions import ConfigLoadError


# =============================================================================
# Shared Fixtures
# =============================================================================

@pytest.fixture
def config_dir(use_real_config_dir):
    """Provide the test config directory."""
    return use_real_config_dir


@pytest.fixture
def clear_singleton():
    """Clear singleton before and after each test."""
    ConfigSingleton._clear_all()
    yield
    ConfigSingleton._clear_all()


# =============================================================================
# Real Config File Tests - Testing All Formats (YAML, JSON, TOML)
# =============================================================================

class TestInstantiateWithRealConfigs:
    """Test instantiation using actual config files.

    These tests load from tests/config/targets/ which contains YAML, JSON,
    and TOML versions of the same config. This ensures format-agnostic behavior.
    """

    def test_instantiate_mssql_from_yaml_config(self, config_dir):
        """Instantiate MSSQLDatabase from YAML config file."""
        loader = ConfigLoader(config_dir=config_dir, profile="target-test", config_format="yaml")
        cfg = loader.load()

        assert "mssql_database" in cfg, "mssql_database not found in YAML config"

        db = instantiate(cfg["mssql_database"])

        # Verify instantiation worked
        from tests.db.mssql.mssql_database_adapter import MSSQLDatabase
        assert isinstance(db, MSSQLDatabase)
        assert db.url == "mssql://localhost"
        assert db.port == 1234
        assert db.database == "test"

    def test_instantiate_mssql_from_json_config(self, config_dir):
        """Instantiate MSSQLDatabase from JSON config file."""
        loader = ConfigLoader(config_dir=config_dir, profile="target-test", config_format="json")
        cfg = loader.load()

        assert "mssql_database" in cfg, "mssql_database not found in JSON config"

        db = instantiate(cfg["mssql_database"])

        from tests.db.mssql.mssql_database_adapter import MSSQLDatabase
        assert isinstance(db, MSSQLDatabase)
        assert db.url == "mssql://localhost"
        assert db.port == 1234
        assert db.database == "test"

    def test_instantiate_mssql_from_toml_config(self, config_dir):
        """Instantiate MSSQLDatabase from TOML config file."""
        loader = ConfigLoader(config_dir=config_dir, profile="target-test", config_format="toml")
        cfg = loader.load()

        assert "mssql_database" in cfg, "mssql_database not found in TOML config"

        db = instantiate(cfg["mssql_database"])

        from tests.db.mssql.mssql_database_adapter import MSSQLDatabase
        assert isinstance(db, MSSQLDatabase)
        assert db.url == "mssql://localhost"
        assert db.port == 1234
        assert db.database == "test"


# =============================================================================
# Integration with @config_inject Tests
# =============================================================================

class TestInstantiateWithConfigInject:
    """Test that instantiated objects work with @config_inject decorator.

    The MSSQLDatabase class uses @config_inject in its connect() method to inject
    username and password from the config. This verifies that _target_ instantiation
    works seamlessly with existing DI patterns.
    """

    def test_mssql_instantiate_and_config_inject_yaml(self, config_dir):
        """Verify MSSQLDatabase instantiation + @config_inject works with YAML."""
        # Initialize ConfigSingleton so @config_inject can resolve values
        ConfigSingleton._clear_all()
        ConfigSingleton.initialize(profile="target-test", config_dir=config_dir)

        try:
            cfg = ConfigSingleton.get()
            db = instantiate(cfg["mssql_database"])

            # Verify the instantiated object can use @config_inject methods
            # The connect() method uses @config_inject to get username/password from config
            assert hasattr(db, "connect"), "MSSQLDatabase should have connect() method"

            # Call connect which uses @config_inject internally
            # This verifies _target_ instantiation integrates with @config_inject
            db.connect()  # Should work without errors

            # Verify the database object has the expected attributes
            assert db.url == "mssql://localhost"
            assert db.port == 1234
            assert db.database == "test"
        finally:
            ConfigSingleton._clear_all()

    def test_mssql_instantiate_and_config_inject_json(self, config_dir):
        """Verify MSSQLDatabase instantiation + @config_inject works with JSON."""
        # Initialize ConfigSingleton with JSON format
        ConfigSingleton._clear_all()
        # Use ConfigLoader directly to load JSON format
        loader = ConfigLoader(config_dir=config_dir, profile="target-test", config_format="json")
        cfg = loader.load()

        # Initialize ConfigSingleton so @config_inject can resolve values
        ConfigSingleton._instance = cfg
        ConfigSingleton._profile = "target-test"
        ConfigSingleton._config_dir = Path(config_dir)

        try:
            db = instantiate(cfg["mssql_database"])

            # Call connect which uses @config_inject
            db.connect()

            assert db.url == "mssql://localhost"
            assert db.port == 1234
            assert db.database == "test"
        finally:
            ConfigSingleton._clear_all()

    def test_mssql_instantiate_and_config_inject_toml(self, config_dir):
        """Verify MSSQLDatabase instantiation + @config_inject works with TOML."""
        # Initialize ConfigSingleton with TOML format
        ConfigSingleton._clear_all()
        # Use ConfigLoader directly to load TOML format
        loader = ConfigLoader(config_dir=config_dir, profile="target-test", config_format="toml")
        cfg = loader.load()

        # Initialize ConfigSingleton so @config_inject can resolve values
        ConfigSingleton._instance = cfg
        ConfigSingleton._profile = "target-test"
        ConfigSingleton._config_dir = Path(config_dir)

        try:
            db = instantiate(cfg["mssql_database"])

            # Call connect which uses @config_inject
            db.connect()

            assert db.url == "mssql://localhost"
            assert db.port == 1234
            assert db.database == "test"
        finally:
            ConfigSingleton._clear_all()


# =============================================================================
# Basic Instantiation Tests (Inline Dicts)
# =============================================================================

class TestInstantiateBasic:
    """Test basic instantiation functionality with inline configs."""

    def test_instantiate_simple_adapter(self, clear_singleton):
        """instantiate() should create instance from _target_."""
        config = {
            "_target_": "tests.test_instantiate.SimpleAdapter",
            "url": "postgres://localhost",
            "port": 5432,
        }

        adapter = instantiate(config)

        assert isinstance(adapter, SimpleAdapter)
        assert adapter.url == "postgres://localhost"
        assert adapter.port == 5432

    def test_instantiate_with_optional_params(self, clear_singleton):
        """instantiate() should handle optional parameters."""
        config = {
            "_target_": "tests.test_instantiate.OptionalParamsAdapter",
            "url": "postgres://localhost",
            "port": 5432,
            "timeout": 60.0,
        }

        adapter = instantiate(config)

        assert isinstance(adapter, OptionalParamsAdapter)
        assert adapter.timeout == 60.0

    def test_instantiate_optional_params_with_defaults(self, clear_singleton):
        """instantiate() should use constructor defaults for missing optional params."""
        config = {
            "_target_": "tests.test_instantiate.OptionalParamsAdapter",
            "url": "postgres://localhost",
        }

        adapter = instantiate(config)

        assert adapter.port == 5432  # default value
        assert adapter.timeout == 30.0  # default value


# =============================================================================
# Type Conversion Tests
# =============================================================================

class TestInstantiateTypeConversion:
    """Test type conversion during instantiation."""

    def test_instantiate_int_conversion_from_string(self, clear_singleton):
        """instantiate() should convert string to int."""
        config = {
            "_target_": "tests.test_instantiate.SimpleAdapter",
            "url": "postgres://localhost",
            "port": "5432",
        }

        adapter = instantiate(config)

        assert isinstance(adapter.port, int)
        assert adapter.port == 5432

    def test_instantiate_float_conversion(self, clear_singleton):
        """instantiate() should convert to float."""
        config = {
            "_target_": "tests.test_instantiate.OptionalParamsAdapter",
            "url": "postgres://localhost",
            "timeout": "45.5",
        }

        adapter = instantiate(config)

        assert isinstance(adapter.timeout, float)
        assert adapter.timeout == 45.5

    def test_instantiate_bool_conversion(self, clear_singleton):
        """instantiate() should convert string booleans."""
        config = {
            "_target_": "tests.test_instantiate.BooleanAdapter",
            "enabled": "true",
        }

        adapter = instantiate(config)
        assert adapter.enabled is True


# =============================================================================
# Recursive Instantiation Tests
# =============================================================================

class TestInstantiateRecursive:
    """Test recursive instantiation of nested _target_ objects."""

    def test_instantiate_nested_target(self, clear_singleton):
        """instantiate() should recursively instantiate nested _target_ objects."""
        config = {
            "_target_": "tests.test_instantiate.NestedAdapter",
            "database": {
                "_target_": "tests.test_instantiate.SimpleAdapter",
                "url": "postgres://localhost",
                "port": 5432,
            },
            "name": "production",
        }

        adapter = instantiate(config)

        assert isinstance(adapter, NestedAdapter)
        assert isinstance(adapter.database, SimpleAdapter)
        assert adapter.database.url == "postgres://localhost"

    def test_instantiate_recursive_false(self, clear_singleton):
        """instantiate() with _recursive_=False should not instantiate nested _target_."""
        config = {
            "_target_": "tests.test_instantiate.NestedAdapter",
            "database": {
                "_target_": "tests.test_instantiate.SimpleAdapter",
                "url": "postgres://localhost",
                "port": 5432,
            },
            "name": "production",
        }

        result = instantiate(config, _recursive_=False)
        assert isinstance(result.database, dict)
        assert result.database["_target_"] == "tests.test_instantiate.SimpleAdapter"


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestInstantiateErrors:
    """Test error handling and validation."""

    def test_instantiate_missing_target_raises(self, clear_singleton):
        """instantiate() should raise ConfigLoadError when _target_ missing."""
        config = {"url": "postgres://localhost", "port": 5432}

        with pytest.raises(ConfigLoadError) as exc_info:
            instantiate(config)

        assert "No _target_ key" in str(exc_info.value)

    def test_instantiate_invalid_target_format_raises(self, clear_singleton):
        """instantiate() should raise ConfigLoadError for invalid _target_ format."""
        config = {
            "_target_": "InvalidFormat",
            "url": "postgres://localhost",
        }

        with pytest.raises(ConfigLoadError) as exc_info:
            instantiate(config)

        assert "Invalid _target_ format" in str(exc_info.value)

    def test_instantiate_module_not_found_raises(self, clear_singleton):
        """instantiate() should raise ConfigLoadError when module not found."""
        config = {
            "_target_": "nonexistent.module.Adapter",
            "url": "postgres://localhost",
        }

        with pytest.raises(ConfigLoadError) as exc_info:
            instantiate(config)

        assert "Module not found" in str(exc_info.value)

    def test_instantiate_class_not_found_raises(self, clear_singleton):
        """instantiate() should raise ConfigLoadError when class not found."""
        config = {
            "_target_": "tests.test_instantiate.NonexistentAdapter",
            "url": "postgres://localhost",
        }

        with pytest.raises(ConfigLoadError) as exc_info:
            instantiate(config)

        assert "not found" in str(exc_info.value).lower()

    def test_instantiate_missing_required_param_raises(self, clear_singleton):
        """instantiate() should raise ConfigLoadError for missing required parameters."""
        config = {
            "_target_": "tests.test_instantiate.SimpleAdapter",
            "url": "postgres://localhost",
        }

        with pytest.raises(ConfigLoadError) as exc_info:
            instantiate(config)

        assert "Missing required parameters" in str(exc_info.value)
        assert "port" in str(exc_info.value)

    def test_instantiate_invalid_type_conversion_raises(self, clear_singleton):
        """instantiate() should raise ConfigLoadError when type conversion fails."""
        config = {
            "_target_": "tests.test_instantiate.SimpleAdapter",
            "url": "postgres://localhost",
            "port": "not-a-number",
        }

        with pytest.raises(ConfigLoadError) as exc_info:
            instantiate(config)

        error_msg = str(exc_info.value).lower()
        assert "failed to convert" in error_msg or "int" in error_msg


# =============================================================================
# Integration Tests
# =============================================================================

class TestInstantiateIntegration:
    """Test instantiate() integration with ConfigSingleton."""

    def test_instantiate_with_dict(self, clear_singleton):
        """instantiate() should work with plain dict config."""
        config = {
            "_target_": "tests.test_instantiate.SimpleAdapter",
            "url": "postgres://localhost",
            "port": 5432,
        }

        adapter = instantiate(config)
        assert isinstance(adapter, SimpleAdapter)


# =============================================================================
# Edge Cases
# =============================================================================

class TestInstantiateEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_instantiate_invalid_config_type_raises(self, clear_singleton):
        """instantiate() should raise ConfigLoadError for invalid input type."""
        with pytest.raises(ConfigLoadError) as exc_info:
            instantiate("not a dict or Config")

        assert "Config or dict" in str(exc_info.value)

    def test_instantiate_empty_config_raises(self, clear_singleton):
        """instantiate() should raise ConfigLoadError for config with no _target_."""
        with pytest.raises(ConfigLoadError) as exc_info:
            instantiate({})

        assert "No _target_ key" in str(exc_info.value)

    def test_instantiate_convert_types_false(self, clear_singleton):
        """instantiate() with _convert_types_=False should skip type conversion."""
        config = {
            "_target_": "tests.test_instantiate.SimpleAdapter",
            "url": "postgres://localhost",
            "port": "5432",
        }

        result = instantiate(config, _convert_types_=False)
        assert result.port == "5432"
        assert isinstance(result.port, str)


# =============================================================================
# Test Helper Classes
# =============================================================================

class SimpleAdapter:
    """Simple adapter with required parameters."""

    def __init__(self, url: str, port: int):
        self.url = url
        self.port = port


class OptionalParamsAdapter:
    """Adapter with optional parameters."""

    def __init__(self, url: str, port: int = 5432, timeout: float = 30.0):
        self.url = url
        self.port = port
        self.timeout = timeout


class BooleanAdapter:
    """Adapter that accepts boolean parameters."""

    def __init__(self, enabled: bool, debug: bool = False):
        self.enabled = enabled
        self.debug = debug


class NestedAdapter:
    """Adapter that accepts another adapter as parameter."""

    def __init__(self, database: SimpleAdapter, name: str):
        self.database = database
        self.name = name
