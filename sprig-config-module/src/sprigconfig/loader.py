import os
import re
import sys
import logging
from pathlib import Path
from typing import Dict, Any
import yaml
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

ENV_PATTERN = re.compile(r"\$\{([^}:]+)(?::([^}]+))?\}")


class ConfigLoadError(Exception):
    """Raised when configuration fails to load or parse."""


def detect_test_profile():
    """Detect pytest runs and default to 'test' profile if none is set."""
    if "pytest" in sys.modules and not os.getenv("APP_PROFILE"):
        logger.debug("Pytest detected. Defaulting APP_PROFILE to 'test'.")
        os.environ["APP_PROFILE"] = "test"


def deep_merge(base: Dict[str, Any], override: Dict[str, Any], suppress_warnings=False, path=""):
    """Merge override into base (in-place)."""
    for key, value in override.items():
        current_path = f"{path}{key}"
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            missing_keys = set(base[key].keys()) - set(value.keys())
            if missing_keys and not suppress_warnings:
                logger.warning(
                    f"Config section '{current_path}' partially overridden; "
                    f"missing keys: {missing_keys}"
                )
            deep_merge(base[key], value, suppress_warnings, current_path + ".")
        else:
            if key in base and base[key] != value:
                logger.info(f"Overriding config '{current_path}'")
            elif key not in base:
                logger.info(f"Adding new config '{current_path}'")
            base[key] = value
    return base


def expand_env_vars(text: str) -> str:
    """Replace ${VAR} or ${VAR:default} with environment values."""
    def replacer(match):
        var, default = match.groups()
        return os.getenv(var, default if default is not None else match.group(0))
    return ENV_PATTERN.sub(replacer, text)


def load_yaml_file(file_path: Path) -> Dict[str, Any]:
    """Load a YAML file if it exists, expand env vars, and parse it."""
    if file_path.exists():
        try:
            text = file_path.read_text()
            expanded = expand_env_vars(text)
            return yaml.safe_load(expanded) or {}
        except yaml.YAMLError as e:
            logger.error(f"Error loading config file {file_path.name}: {e}")
            raise ConfigLoadError(f"Invalid YAML in {file_path.name}: {e}")
    return {}


def decrypt_secret(value: str) -> str:
    """Decrypt ENC(...) values using Fernet key from APP_SECRET_KEY."""
    if not (value.startswith("ENC(") and value.endswith(")")):
        return value
    
    key = os.getenv("APP_SECRET_KEY")
    if not key:
        raise ConfigLoadError("APP_SECRET_KEY is required to decrypt secrets")
    
    fernet = Fernet(key.encode() if isinstance(key, str) else key)
    encrypted_data = value[4:-1].encode()
    return fernet.decrypt(encrypted_data).decode()


def process_secrets(config: Dict[str, Any]):
    """Walk through config and decrypt secrets if encrypted: true."""
    secrets = config.get("app", {}).get("secrets", {})
    if secrets.get("encrypted") is True:
        for k, v in secrets.items():
            if isinstance(v, str) and v.startswith("ENC("):
                secrets[k] = decrypt_secret(v)


def load_config(profile: str = None, config_dir: Path = None) -> Dict[str, Any]:
    detect_test_profile()
    
    active_profile = profile or os.getenv("APP_PROFILE", "dev")

    # Config directory defaults to ./config relative to caller
    if config_dir is None:
        config_dir = Path(
            os.getenv("APP_CONFIG_DIR", Path.cwd() / "config")
        ).resolve()

    logger.debug(f"Using config directory: {config_dir}")

    # Load base config
    base_file = config_dir / "application.yml"
    if not base_file.exists():
        if active_profile in ("prod", "test"):
            raise ConfigLoadError(
                f"Base config application.yml is required for profile '{active_profile}', "
                f"but was not found in {config_dir}"
            )
        logger.warning("No application.yml found. Using empty defaults.")
        base_config = {}
    else:
        base_config = load_yaml_file(base_file)

    suppress_warnings = base_config.get("suppress_config_merge_warnings", False)

    # Load profile config
    profile_file = config_dir / f"application-{active_profile}.yml"
    if profile_file.exists():
        logger.info(f"Loading profile config: {profile_file.name}")
        profile_config = load_yaml_file(profile_file)
        suppress_warnings = profile_config.get(
            "suppress_config_merge_warnings", suppress_warnings
        )
        base_config = deep_merge(base_config, profile_config, suppress_warnings)
    else:
        if active_profile in ("prod", "test"):
            raise ConfigLoadError(
                f"Profile '{active_profile}' requires {profile_file.name}, "
                f"but it was not found in {config_dir}"
            )
        if not base_config.get("suppress_profile_not_found_warning", False):
            logger.warning(
                f"No profile config found for profile '{active_profile}'. "
                f"Continuing with base config."
            )

    # Handle imports
    imports = base_config.get("imports", [])
    if imports:
        logger.info(f"Found config imports: {imports}")
        for import_path in imports:
            import_file = (config_dir / import_path).resolve()
            if import_file.exists():
                logger.info(f"Importing additional config: {import_file.name}")
                imported_config = load_yaml_file(import_file)
                base_config = deep_merge(base_config, imported_config, suppress_warnings)
            else:
                logger.warning(f"Import file not found: {import_path}")

    # Production checks
    if active_profile == "prod":
        log_level = base_config.get("logging", {}).get("level")
        allow_debug = base_config.get("allow_debug_in_prod", False)

        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

        if "level" not in base_config.get("logging", {}) or base_config["logging"]["level"] is None:
            logger.warning("No logging.level set in production; defaulting to INFO.")
            base_config.setdefault("logging", {})["level"] = "INFO"

        elif log_level.upper() not in valid_levels:
            logger.warning(f"Invalid logging.level '{log_level}' in production; defaulting to INFO.")
            base_config["logging"]["level"] = "INFO"

        elif log_level.upper() == "DEBUG" and not allow_debug:
            raise ConfigLoadError(
                "DEBUG logging is not allowed in production without allow_debug_in_prod: true"
            )

        elif log_level.upper() == "DEBUG" and allow_debug:
            logger.warning("DEBUG logging is enabled in production via allow_debug_in_prod.")

    else:
        base_config.setdefault("logging", {}).setdefault("level", "INFO")

    process_secrets(base_config)
    
    logger.info(f"Active profile: {active_profile}")
    return base_config
