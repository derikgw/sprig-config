import os
import re
import sys
import logging
from pathlib import Path
from typing import Dict, Any
import yaml
from cryptography.fernet import Fernet
from sprigconfig.lazy_secret import LazySecret
from sprigconfig.exceptions import ConfigLoadError

logger = logging.getLogger(__name__)

ENV_PATTERN = re.compile(r"\$\{([^}:]+)(?::([^}]+))?\}")


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
    """Load a YAML file if it exists, expand env vars, and parse it (BOM-safe)."""
    if file_path.exists():
        try:
            text = file_path.read_text(encoding="utf-8-sig")  # strip BOM if present
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
    """
    Traverse config and wrap ENC(...) values in LazySecret.
    No 'secrets:' block or 'encrypted: true' flag required.
    Decryption happens lazily when the LazySecret is accessed.
    """
    def recurse(node):
        if isinstance(node, dict):
            for k, v in list(node.items()):
                if isinstance(v, str) and v.startswith("ENC(") and v.endswith(")"):
                    node[k] = LazySecret(v)
                elif isinstance(v, dict):
                    recurse(v)
                elif isinstance(v, list):
                    for idx, item in enumerate(v):
                        if isinstance(item, str) and item.startswith("ENC(") and item.endswith(")"):
                            v[idx] = LazySecret(item)
                        elif isinstance(item, dict):
                            recurse(item)
        return node

    recurse(config)


def load_config(profile: str = None, config_dir: Path = None) -> Dict[str, Any]:
    # Config directory defaults to ./config relative to CWD or APP_CONFIG_DIR
    if config_dir is None:
        config_dir = Path(os.getenv("APP_CONFIG_DIR", Path.cwd() / "config")).resolve()

    logger.debug(f"Using config directory: {config_dir}")

    # Load base config
    base_file = config_dir / "application.yml"
    if base_file.exists():
        base_config = load_yaml_file(base_file)
    else:
        logger.warning("No application.yml found. Using empty defaults.")
        base_config = {}

    # Determine active profile (env/param only — do NOT *select* from files)
    yml_profile = base_config.get("app", {}).get("profile")  # only used to warn on conflicts
    active_profile = (
        profile
        or os.getenv("APP_PROFILE")
        or ("test" if "pytest" in sys.modules else "dev")
    )

    # Warn if files specify a different app.profile than the runtime-selected one
    if yml_profile and yml_profile != active_profile:
        logger.warning(
            "Ignoring app.profile from files (%s); using active profile %s. "
            "Consider removing app.profile from files to avoid confusion.",
            yml_profile, active_profile
        )

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

        if not log_level:
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

    # Wrap ENC(...) values with LazySecret
    process_secrets(base_config)

    # Inject the active profile into the final config (env wins over files)
    base_config.setdefault("app", {})
    base_config["app"]["profile"] = active_profile

    logger.info(f"Active profile: {active_profile}")
    return base_config
