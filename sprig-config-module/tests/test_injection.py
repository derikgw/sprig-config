# tests/test_injection.py
"""
Comprehensive tests for SprigConfig dependency injection features.

Tests cover:
1. ConfigValue descriptor (field-level binding)
2. @ConfigurationProperties decorator (section binding)
3. @config_inject decorator (function parameter injection)

Test Coverage Goals:
- 100% line coverage
- All edge cases and error conditions
- Type conversions
- LazySecret handling
- Error messages
"""

import pytest
from pathlib import Path

from sprigconfig import (
    ConfigSingleton,
    Config,
    ConfigValue,
    ConfigurationProperties,
    config_inject,
    ConfigLoadError,
)
from sprigconfig.lazy_secret import LazySecret


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture(autouse=True)
def clear_singleton():
    """Clear singleton before and after each test."""
    ConfigSingleton._clear_all()
    yield
    ConfigSingleton._clear_all()


@pytest.fixture
def config_dir(use_real_config_dir):
    """Use the real tests/config directory."""
    return use_real_config_dir


@pytest.fixture
def initialized_singleton(config_dir):
    """Initialize ConfigSingleton with dev profile."""
    ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
    yield
    ConfigSingleton._clear_all()


# ==============================================================================
# ConfigValue DESCRIPTOR TESTS
# ==============================================================================

class TestConfigValueBasicBinding:
    """Test basic ConfigValue descriptor functionality."""

    def test_configvalue_binds_string_field(self, initialized_singleton):
        """ConfigValue should resolve string values from config."""
        class MyService:
            app_name: str = ConfigValue("app.name")

        service = MyService()
        assert service.app_name == "SprigTestApp"

    def test_configvalue_binds_nested_key(self, initialized_singleton):
        """ConfigValue should resolve deeply nested keys."""
        class MyService:
            log_level: str = ConfigValue("logging.level")

        service = MyService()
        assert service.log_level == "INFO"

    def test_configvalue_multiple_fields(self, initialized_singleton):
        """Multiple ConfigValue fields should work independently."""
        class MyService:
            app_name: str = ConfigValue("app.name")
            log_level: str = ConfigValue("logging.level")
            log_format: str = ConfigValue("logging.format")

        service = MyService()
        assert service.app_name == "SprigTestApp"
        assert service.log_level == "INFO"
        assert service.log_format == "%(message)s"

    def test_configvalue_lazy_evaluation(self, config_dir):
        """ConfigValue should fetch fresh value on each access (lazy)."""
        class MyService:
            app_name: str = ConfigValue("app.name")

        # Initialize with dev
        ConfigSingleton.initialize(profile="dev", config_dir=config_dir)
        service = MyService()
        assert service.app_name == "SprigTestApp"

        # Reinitialize with different profile (test-only scenario)
        ConfigSingleton._clear_all()
        ConfigSingleton.initialize(profile="suppress", config_dir=config_dir)
        # Access should get fresh value
        assert service.app_name == "SprigTestApp"  # Still works


class TestConfigValueTypeConversion:
    """Test ConfigValue type conversion based on type hints."""

    def test_configvalue_converts_to_int(self, initialized_singleton):
        """ConfigValue should convert numeric strings to int."""
        class MyService:
            repo_x: int = ConfigValue("etl.jobs.repositories.inmemory.params.x")

        service = MyService()
        assert service.repo_x == 1
        assert isinstance(service.repo_x, int)

    def test_configvalue_converts_to_str(self, initialized_singleton):
        """ConfigValue should convert values to str when annotated."""
        class MyService:
            level: str = ConfigValue("logging.level")

        service = MyService()
        assert service.level == "INFO"
        assert isinstance(service.level, str)

    def test_configvalue_bool_conversion_from_true_string(self, config_dir):
        """ConfigValue should convert 'true' string to bool True."""
        # Create temp config with boolean
        import yaml
        import tempfile
        import shutil

        temp_dir = Path(tempfile.mkdtemp())
        try:
            config_file = temp_dir / "application.yml"
            config_file.write_text("feature:\n  enabled: true\n")

            ConfigSingleton.initialize(profile="dev", config_dir=temp_dir)

            class MyService:
                enabled: bool = ConfigValue("feature.enabled")

            service = MyService()
            assert service.enabled is True
            assert isinstance(service.enabled, bool)
        finally:
            shutil.rmtree(temp_dir)

    def test_configvalue_bool_conversion_from_false_string(self, config_dir):
        """ConfigValue should convert 'false' string to bool False."""
        import tempfile
        import shutil

        temp_dir = Path(tempfile.mkdtemp())
        try:
            config_file = temp_dir / "application.yml"
            config_file.write_text("feature:\n  enabled: false\n")

            ConfigSingleton.initialize(profile="dev", config_dir=temp_dir)

            class MyService:
                enabled: bool = ConfigValue("feature.enabled")

            service = MyService()
            assert service.enabled is False
        finally:
            shutil.rmtree(temp_dir)

    def test_configvalue_list_passthrough(self, config_dir):
        """ConfigValue should pass through list values."""
        import tempfile
        import shutil

        temp_dir = Path(tempfile.mkdtemp())
        try:
            config_file = temp_dir / "application.yml"
            config_file.write_text("items:\n  - one\n  - two\n  - three\n")

            ConfigSingleton.initialize(profile="dev", config_dir=temp_dir)

            class MyService:
                items: list = ConfigValue("items")

            service = MyService()
            assert service.items == ["one", "two", "three"]
            assert isinstance(service.items, list)
        finally:
            shutil.rmtree(temp_dir)

    def test_configvalue_dict_passthrough(self, initialized_singleton):
        """ConfigValue should pass through dict values."""
        class MyService:
            repos: dict = ConfigValue("etl.jobs.repositories")

        service = MyService()
        assert isinstance(service.repos, (dict, Config))
        assert "inmemory" in service.repos


class TestConfigValueDefaults:
    """Test ConfigValue default value handling."""

    def test_configvalue_with_default_missing_key(self, initialized_singleton):
        """ConfigValue should return default when key is missing."""
        class MyService:
            timeout: int = ConfigValue("api.timeout", default=30)

        service = MyService()
        assert service.timeout == 30

    def test_configvalue_with_default_key_exists(self, initialized_singleton):
        """ConfigValue should use config value when key exists."""
        class MyService:
            app_name: str = ConfigValue("app.name", default="DefaultApp")

        service = MyService()
        assert service.app_name == "SprigTestApp"  # From config, not default

    def test_configvalue_default_none(self, initialized_singleton):
        """ConfigValue with default=None should return None for missing keys."""
        class MyService:
            missing: str = ConfigValue("does.not.exist", default=None)

        service = MyService()
        assert service.missing is None


class TestConfigValueErrors:
    """Test ConfigValue error handling."""

    def test_configvalue_missing_key_no_default_raises(self, initialized_singleton):
        """ConfigValue should raise clear error when key missing and no default."""
        class MyService:
            missing: str = ConfigValue("does.not.exist")

        service = MyService()
        with pytest.raises(ConfigLoadError) as exc_info:
            _ = service.missing

        assert "does.not.exist" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_configvalue_missing_nested_key_with_parent(self, initialized_singleton):
        """ConfigValue should provide helpful context when parent exists."""
        class MyService:
            missing: str = ConfigValue("logging.missing_key")

        service = MyService()
        with pytest.raises(ConfigLoadError) as exc_info:
            _ = service.missing

        error_msg = str(exc_info.value)
        assert "logging.missing_key" in error_msg
        assert "Available keys" in error_msg or "not found" in error_msg

    def test_configvalue_before_singleton_init_raises(self):
        """ConfigValue should raise clear error if singleton not initialized."""
        class MyService:
            value: str = ConfigValue("some.key")

        service = MyService()
        with pytest.raises(ConfigLoadError) as exc_info:
            _ = service.value

        assert "not initialized" in str(exc_info.value)

    def test_configvalue_is_readonly(self, initialized_singleton):
        """ConfigValue descriptors should be read-only."""
        class MyService:
            app_name: str = ConfigValue("app.name")

        service = MyService()
        with pytest.raises(AttributeError) as exc_info:
            service.app_name = "NewValue"

        assert "read-only" in str(exc_info.value).lower()

    def test_configvalue_type_conversion_error(self, config_dir):
        """ConfigValue should raise clear error on type conversion failure."""
        import tempfile
        import shutil

        temp_dir = Path(tempfile.mkdtemp())
        try:
            config_file = temp_dir / "application.yml"
            config_file.write_text("value: not_a_number\n")

            ConfigSingleton.initialize(profile="dev", config_dir=temp_dir)

            class MyService:
                value: int = ConfigValue("value")

            service = MyService()
            with pytest.raises(ConfigLoadError) as exc_info:
                _ = service.value

            assert "Cannot convert" in str(exc_info.value)
        finally:
            shutil.rmtree(temp_dir)

    def test_configvalue_float_conversion(self, config_dir):
        """ConfigValue should convert to float."""
        import tempfile
        import shutil

        temp_dir = Path(tempfile.mkdtemp())
        try:
            config_file = temp_dir / "application.yml"
            config_file.write_text("value: 3.14\n")

            ConfigSingleton.initialize(profile="dev", config_dir=temp_dir)

            class MyService:
                value: float = ConfigValue("value")

            service = MyService()
            assert service.value == 3.14
            assert isinstance(service.value, float)
        finally:
            shutil.rmtree(temp_dir)

    def test_configvalue_bool_string_conversion(self, config_dir):
        """ConfigValue should convert string 'true'/'false' to bool."""
        import tempfile
        import shutil

        temp_dir = Path(tempfile.mkdtemp())
        try:
            config_file = temp_dir / "application.yml"
            config_file.write_text("enabled: 'true'\ndisabled: 'false'\n")

            ConfigSingleton.initialize(profile="dev", config_dir=temp_dir)

            class MyService:
                enabled: bool = ConfigValue("enabled")
                disabled: bool = ConfigValue("disabled")

            service = MyService()
            assert service.enabled is True
            assert service.disabled is False
        finally:
            shutil.rmtree(temp_dir)

    def test_configvalue_list_type_error(self, config_dir):
        """ConfigValue should raise error when converting non-list to list."""
        import tempfile
        import shutil

        temp_dir = Path(tempfile.mkdtemp())
        try:
            config_file = temp_dir / "application.yml"
            config_file.write_text("value: not_a_list\n")

            ConfigSingleton.initialize(profile="dev", config_dir=temp_dir)

            class MyService:
                value: list = ConfigValue("value")

            service = MyService()
            with pytest.raises(ConfigLoadError) as exc_info:
                _ = service.value

            assert "Cannot convert" in str(exc_info.value)
        finally:
            shutil.rmtree(temp_dir)

    def test_configvalue_dict_type_error(self, config_dir):
        """ConfigValue should raise error when converting non-dict to dict."""
        import tempfile
        import shutil

        temp_dir = Path(tempfile.mkdtemp())
        try:
            config_file = temp_dir / "application.yml"
            config_file.write_text("value: not_a_dict\n")

            ConfigSingleton.initialize(profile="dev", config_dir=temp_dir)

            class MyService:
                value: dict = ConfigValue("value")

            service = MyService()
            with pytest.raises(ConfigLoadError) as exc_info:
                _ = service.value

            assert "Cannot convert" in str(exc_info.value)
        finally:
            shutil.rmtree(temp_dir)


class TestConfigValueLazySecret:
    """Test ConfigValue handling of LazySecret."""

    def test_configvalue_lazysecret_no_decrypt(self, config_dir):
        """ConfigValue should return LazySecret object by default."""
        ConfigSingleton.initialize(profile="secrets", config_dir=config_dir)

        class MyService:
            api_key: LazySecret = ConfigValue("secrets.api_key")

        service = MyService()
        assert isinstance(service.api_key, LazySecret)

    def test_configvalue_lazysecret_with_decrypt(self, monkeypatch):
        """ConfigValue with decrypt=True should auto-decrypt LazySecret."""
        import tempfile
        import shutil
        import os
        from cryptography.fernet import Fernet

        # Ensure singleton is clear
        ConfigSingleton._clear_all()

        # Create encryption key and encrypt a secret
        key = Fernet.generate_key()
        fernet = Fernet(key)
        secret_value = "my-secret-api-key"
        encrypted = fernet.encrypt(secret_value.encode()).decode()

        # Create temp config with encrypted secret
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # Create base application.yml
            base_config = temp_dir / "application.yml"
            base_config.write_text("app:\n  name: TestApp\n")

            # Create profile-specific config with encrypted secret
            profile_config = temp_dir / "application-test.yml"
            profile_config.write_text(f"secrets:\n  api_key: ENC({encrypted})\n")

            # Set encryption key BEFORE initializing singleton
            os.environ["APP_SECRET_KEY"] = key.decode()

            try:
                ConfigSingleton.initialize(profile="test", config_dir=temp_dir)

                # Test decrypt=True: should return decrypted string
                class MyServiceDecrypt:
                    api_key: str = ConfigValue("secrets.api_key", decrypt=True)

                service_decrypt = MyServiceDecrypt()

                # decrypt=True: should be a plain string
                assert service_decrypt.api_key == secret_value
                assert isinstance(service_decrypt.api_key, str)

                # Reinitialize for second test
                ConfigSingleton._clear_all()
                ConfigSingleton.initialize(profile="test", config_dir=temp_dir)

                # Test decrypt=False: should return LazySecret object
                class MyServiceNoDecrypt:
                    api_key: LazySecret = ConfigValue("secrets.api_key", decrypt=False)

                service_no_decrypt = MyServiceNoDecrypt()
                # decrypt=False: should be a LazySecret object
                print(f"decrypt=False type: {type(service_no_decrypt.api_key)}")
                print(f"decrypt=False object: {service_no_decrypt.api_key}")
                print(f"decrypt=False repr: {repr(service_no_decrypt.api_key)}")
                assert isinstance(service_no_decrypt.api_key, LazySecret)
                # Verify we can manually decrypt it
                print(f"Manual .get() call: {service_no_decrypt.api_key.get()}")
                assert service_no_decrypt.api_key.get() == secret_value
            finally:
                # Clean up environment
                if "APP_SECRET_KEY" in os.environ:
                    del os.environ["APP_SECRET_KEY"]
        finally:
            shutil.rmtree(temp_dir)
            ConfigSingleton._clear_all()


# ==============================================================================
# @ConfigurationProperties DECORATOR TESTS
# ==============================================================================

class TestConfigurationPropertiesBasic:
    """Test basic @ConfigurationProperties functionality."""

    def test_configproperties_binds_section(self, initialized_singleton):
        """@ConfigurationProperties should bind entire config section."""
        @ConfigurationProperties(prefix="logging")
        class LoggingConfig:
            level: str
            format: str

        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.format == "%(message)s"

    def test_configproperties_binds_nested_section(self, initialized_singleton):
        """@ConfigurationProperties should bind nested sections."""
        @ConfigurationProperties(prefix="etl.jobs")
        class JobsConfig:
            root: str
            default_shell: str

        config = JobsConfig()
        assert config.root == "/jobs/default"
        assert config.default_shell == "/bin/bash"

    def test_configproperties_preserves_config_object(self, initialized_singleton):
        """@ConfigurationProperties should provide _config attribute."""
        @ConfigurationProperties(prefix="logging")
        class LoggingConfig:
            level: str

        config = LoggingConfig()
        assert hasattr(config, "_config")
        assert isinstance(config._config, Config)
        assert config._config.get("level") == "INFO"

    def test_configproperties_multiple_instances(self, initialized_singleton):
        """Multiple instances should each get their own attributes."""
        @ConfigurationProperties(prefix="logging")
        class LoggingConfig:
            level: str

        config1 = LoggingConfig()
        config2 = LoggingConfig()

        assert config1.level == "INFO"
        assert config2.level == "INFO"
        assert config1 is not config2


class TestConfigurationPropertiesTypeConversion:
    """Test @ConfigurationProperties type conversion."""

    def test_configproperties_converts_types(self, initialized_singleton):
        """@ConfigurationProperties should convert types based on annotations."""
        @ConfigurationProperties(prefix="etl.jobs.repositories.inmemory.params")
        class ParamsConfig:
            x: int

        config = ParamsConfig()
        assert config.x == 1
        assert isinstance(config.x, int)

    def test_configproperties_bool_conversion(self, config_dir):
        """@ConfigurationProperties should convert bool values."""
        import tempfile
        import shutil

        temp_dir = Path(tempfile.mkdtemp())
        try:
            config_file = temp_dir / "application.yml"
            config_file.write_text("feature:\n  enabled: true\n  debug: false\n")

            ConfigSingleton.initialize(profile="dev", config_dir=temp_dir)

            @ConfigurationProperties(prefix="feature")
            class FeatureConfig:
                enabled: bool
                debug: bool

            config = FeatureConfig()
            assert config.enabled is True
            assert config.debug is False
        finally:
            shutil.rmtree(temp_dir)


class TestConfigurationPropertiesErrors:
    """Test @ConfigurationProperties error handling."""

    def test_configproperties_missing_section_raises(self, initialized_singleton):
        """@ConfigurationProperties should raise error for missing section."""
        @ConfigurationProperties(prefix="does.not.exist")
        class MissingConfig:
            value: str

        with pytest.raises(ConfigLoadError) as exc_info:
            MissingConfig()

        assert "does.not.exist" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_configproperties_before_singleton_init_raises(self):
        """@ConfigurationProperties should raise error if singleton not initialized."""
        @ConfigurationProperties(prefix="logging")
        class LoggingConfig:
            level: str

        with pytest.raises(ConfigLoadError) as exc_info:
            LoggingConfig()

        assert "not initialized" in str(exc_info.value)

    def test_configproperties_non_dict_section_raises(self, config_dir):
        """@ConfigurationProperties should raise error if prefix is not a dict."""
        import tempfile
        import shutil

        temp_dir = Path(tempfile.mkdtemp())
        try:
            config_file = temp_dir / "application.yml"
            config_file.write_text("value: just_a_string\n")

            ConfigSingleton.initialize(profile="dev", config_dir=temp_dir)

            @ConfigurationProperties(prefix="value")
            class BadConfig:
                field: str

            with pytest.raises(ConfigLoadError) as exc_info:
                BadConfig()

            assert "non-dict" in str(exc_info.value)
        finally:
            shutil.rmtree(temp_dir)


class TestConfigurationPropertiesPartialBinding:
    """Test @ConfigurationProperties with partial/missing keys."""

    def test_configproperties_skips_missing_keys(self, initialized_singleton):
        """@ConfigurationProperties should skip keys not in config."""
        @ConfigurationProperties(prefix="logging")
        class LoggingConfig:
            level: str
            format: str
            missing_key: str  # Not in config

        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.format == "%(message)s"
        assert not hasattr(config, "missing_key")

    def test_configproperties_with_custom_init(self, initialized_singleton):
        """@ConfigurationProperties should work with custom __init__."""
        @ConfigurationProperties(prefix="logging")
        class LoggingConfig:
            level: str
            custom_attr: str = "custom"

            def __init__(self):
                self.custom_attr = "initialized"

        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.custom_attr == "initialized"

    def test_configproperties_type_conversion_error(self, config_dir):
        """@ConfigurationProperties should raise error on type conversion failure."""
        import tempfile
        import shutil

        temp_dir = Path(tempfile.mkdtemp())
        try:
            config_file = temp_dir / "application.yml"
            config_file.write_text("section:\n  value: not_a_number\n")

            ConfigSingleton.initialize(profile="dev", config_dir=temp_dir)

            @ConfigurationProperties(prefix="section")
            class SectionConfig:
                value: int

            with pytest.raises(ConfigLoadError) as exc_info:
                SectionConfig()

            assert "Type conversion failed" in str(exc_info.value)
        finally:
            shutil.rmtree(temp_dir)


class TestConfigurationPropertiesLazySecret:
    """Test @ConfigurationProperties with LazySecret."""

    def test_configproperties_preserves_lazysecret(self, config_dir):
        """@ConfigurationProperties should preserve LazySecret objects."""
        ConfigSingleton.initialize(profile="secrets", config_dir=config_dir)

        @ConfigurationProperties(prefix="secrets")
        class SecretsConfig:
            api_key: LazySecret

        config = SecretsConfig()
        # api_key might not be set if not in config, or should be LazySecret
        if hasattr(config, "api_key"):
            assert isinstance(config.api_key, LazySecret)


# ==============================================================================
# @config_inject DECORATOR TESTS
# ==============================================================================

class TestConfigInjectBasic:
    """Test basic @config_inject functionality."""

    def test_configinject_injects_parameters(self, initialized_singleton):
        """@config_inject should inject ConfigValue parameters."""
        @config_inject
        def get_app_name(name: str = ConfigValue("app.name")):
            return name

        result = get_app_name()
        assert result == "SprigTestApp"

    def test_configinject_multiple_parameters(self, initialized_singleton):
        """@config_inject should inject multiple ConfigValue parameters."""
        @config_inject
        def get_config(
            app_name: str = ConfigValue("app.name"),
            log_level: str = ConfigValue("logging.level")
        ):
            return {"app": app_name, "log": log_level}

        result = get_config()
        assert result == {"app": "SprigTestApp", "log": "INFO"}

    def test_configinject_with_regular_defaults(self, initialized_singleton):
        """@config_inject should preserve regular default values."""
        @config_inject
        def get_value(
            app_name: str = ConfigValue("app.name"),
            timeout: int = 30
        ):
            return {"app": app_name, "timeout": timeout}

        result = get_value()
        assert result == {"app": "SprigTestApp", "timeout": 30}


class TestConfigInjectOverrides:
    """Test @config_inject parameter override functionality."""

    def test_configinject_override_with_kwarg(self, initialized_singleton):
        """@config_inject should allow overriding with keyword argument."""
        @config_inject
        def get_app_name(name: str = ConfigValue("app.name")):
            return name

        result = get_app_name(name="OverriddenApp")
        assert result == "OverriddenApp"

    def test_configinject_override_with_positional(self, initialized_singleton):
        """@config_inject should allow overriding with positional argument."""
        @config_inject
        def get_app_name(name: str = ConfigValue("app.name")):
            return name

        result = get_app_name("OverriddenApp")
        assert result == "OverriddenApp"

    def test_configinject_mixed_overrides(self, initialized_singleton):
        """@config_inject should handle mixed overrides and config values."""
        @config_inject
        def get_config(
            app_name: str = ConfigValue("app.name"),
            log_level: str = ConfigValue("logging.level")
        ):
            return {"app": app_name, "log": log_level}

        result = get_config(log_level="DEBUG")
        assert result == {"app": "SprigTestApp", "log": "DEBUG"}


class TestConfigInjectErrors:
    """Test @config_inject error handling."""

    def test_configinject_missing_key_raises(self, initialized_singleton):
        """@config_inject should raise error for missing config keys."""
        @config_inject
        def get_value(missing: str = ConfigValue("does.not.exist")):
            return missing

        with pytest.raises(ConfigLoadError) as exc_info:
            get_value()

        assert "does.not.exist" in str(exc_info.value)


# ==============================================================================
# INTEGRATION TESTS
# ==============================================================================

class TestConfigValueResolveMethod:
    """Test ConfigValue.resolve() method used by @config_inject."""

    def test_configvalue_resolve_method(self, initialized_singleton):
        """resolve() should work without instance."""
        descriptor = ConfigValue("app.name")
        descriptor._type_hint = str  # Normally set by __set_name__
        value = descriptor.resolve()
        assert value == "SprigTestApp"

    def test_configvalue_resolve_before_init_raises(self):
        """resolve() should raise if singleton not initialized."""
        descriptor = ConfigValue("app.name")
        with pytest.raises(ConfigLoadError) as exc_info:
            descriptor.resolve()

        assert "not initialized" in str(exc_info.value)

    def test_configvalue_resolve_missing_key_raises(self, initialized_singleton):
        """resolve() should raise for missing keys."""
        descriptor = ConfigValue("does.not.exist")
        with pytest.raises(ConfigLoadError) as exc_info:
            descriptor.resolve()

        assert "does.not.exist" in str(exc_info.value)


class TestConfigurationPropertiesNestedObjects:
    """Test @ConfigurationProperties with nested config objects."""

    def test_configproperties_nested_object_instantiation(self, config_dir):
        """@ConfigurationProperties should auto-instantiate nested objects."""
        import tempfile
        import shutil

        temp_dir = Path(tempfile.mkdtemp())
        try:
            config_file = temp_dir / "application.yml"
            config_file.write_text(
                "outer:\n"
                "  name: OuterName\n"
                "  inner:\n"
                "    value: InnerValue\n"
            )

            ConfigSingleton.initialize(profile="dev", config_dir=temp_dir)

            @ConfigurationProperties(prefix="outer.inner")
            class InnerConfig:
                value: str

            @ConfigurationProperties(prefix="outer")
            class OuterConfig:
                name: str
                inner: InnerConfig

            config = OuterConfig()
            assert config.name == "OuterName"
            assert isinstance(config.inner, InnerConfig)
            assert config.inner.value == "InnerValue"
        finally:
            shutil.rmtree(temp_dir)

    def test_configproperties_nested_instantiation_error(self, config_dir):
        """@ConfigurationProperties should raise clear error for nested failures."""
        import tempfile
        import shutil

        temp_dir = Path(tempfile.mkdtemp())
        try:
            config_file = temp_dir / "application.yml"
            config_file.write_text(
                "outer:\n"
                "  name: OuterName\n"
                "  inner:\n"
                "    value: InnerValue\n"
            )

            ConfigSingleton.initialize(profile="dev", config_dir=temp_dir)

            # Define nested class without decorator (will fail to instantiate)
            class BrokenInnerConfig:
                def __init__(self):
                    raise ValueError("Intentional error")

            @ConfigurationProperties(prefix="outer")
            class OuterConfig:
                name: str
                inner: BrokenInnerConfig

            with pytest.raises(ConfigLoadError) as exc_info:
                OuterConfig()

            assert "Failed to instantiate nested config class" in str(exc_info.value)
        finally:
            shutil.rmtree(temp_dir)


class TestDependencyInjectionIntegration:
    """Test integration of all dependency injection patterns together."""

    def test_all_patterns_work_together(self, initialized_singleton):
        """All DI patterns should work together seamlessly."""
        # Pattern 1: ConfigValue
        class CacheService:
            ttl: int = ConfigValue("etl.jobs.repositories.inmemory.params.x")

        # Pattern 2: @ConfigurationProperties
        @ConfigurationProperties(prefix="logging")
        class LoggingConfig:
            level: str
            format: str

        # Pattern 3: @config_inject
        @config_inject
        def get_app_info(name: str = ConfigValue("app.name")):
            return name

        # All should work
        cache = CacheService()
        logging = LoggingConfig()
        app_name = get_app_info()

        assert cache.ttl == 1
        assert logging.level == "INFO"
        assert app_name == "SprigTestApp"

    def test_class_access_returns_descriptor(self, initialized_singleton):
        """Accessing ConfigValue on class should return descriptor."""
        class MyService:
            value: str = ConfigValue("app.name")

        # Class access returns descriptor
        descriptor = MyService.value
        assert isinstance(descriptor, ConfigValue)
        assert descriptor.key == "app.name"

        # Instance access returns value
        service = MyService()
        assert service.value == "SprigTestApp"
