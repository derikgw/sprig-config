# src/sprigconfig/loader.py
import os
import re
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
    Uses APP_SECRET_KEY from environment if available,
    otherwise leaves LazySecret undecodable until accessed.
    """
    key = os.getenv("APP_SECRET_KEY")

    def recurse(node):
        if isinstance(node, dict):
            for k, v in list(node.items()):
                if isinstance(v, str) and v.startswith("ENC(") and v.endswith(")"):
                    node[k] = LazySecret(v, key=key)
                elif isinstance(v, dict):
                    recurse(v)
                elif isinstance(v, list):
                    for idx, item in enumerate(v):
                        if isinstance(item, str) and item.startswith("ENC(") and item.endswith(")"):
                            v[idx] = LazySecret(item, key=key)
                        elif isinstance(item, dict):
                            recurse(item)
        return node

    recurse(config)


def load_config(profile: str, config_dir: Path) -> Dict[str, Any]:
    """
    Loads base (application.yml) and optional profile config (application-{profile}.yml).
    Missing profile file does not raise an error — only logs a warning.
    Applications using SprigConfig can decide if that's acceptable.
    """
    logger.debug(f"Using config directory: {config_dir}")

    # --- 1️⃣ Load base config ---
    base_file = config_dir / "application.yml"
    if not base_file.exists():
        raise ConfigLoadError(f"Missing required base config: {base_file}")
    base_config = load_yaml_file(base_file)
    suppress_warnings = base_config.get("suppress_config_merge_warnings", False)

    # --- 2️⃣ Load profile config (optional) ---
    profile_config = {}
    profile_file = config_dir / f"application-{profile}.yml"
    if profile_file.exists():
        logger.info(f"Loading profile config: {profile_file.name}")
        profile_config = load_yaml_file(profile_file)
    else:
        logger.warning(
            f"Missing profile config for '{profile}' in {config_dir}; continuing with base config only"
        )

    # 🔹 Check for suppress flag before merging, in case it's defined in profile
    pre_suppress = profile_config.get("suppress_config_merge_warnings", False)
    suppress_warnings = suppress_warnings or pre_suppress

    # --- Merge base + profile ---
    config = deep_merge(base_config, profile_config, suppress_warnings)

    # 🔹 Refresh suppression flag after merge for later imports
    suppress_warnings = config.get("suppress_config_merge_warnings", suppress_warnings)

    # --- 3️⃣ Handle imports (optional) ---
    for import_path in config.get("imports", []):
        import_file = (config_dir / import_path).resolve()
        if not import_file.exists():
            logger.warning(f"Import file not found: {import_file}")
            continue
        logger.info(f"Importing additional config: {import_file.name}")
        imported_config = load_yaml_file(import_file)
        config = deep_merge(config, imported_config, suppress_warnings)

    # --- 4️⃣ Warn if file defines a conflicting app.profile ---
    file_profile = config.get("app", {}).get("profile")
    if file_profile and file_profile != profile:
        logger.warning(
            f"Ignoring app.profile from files ({file_profile}); using active profile {profile}."
        )

    # --- 5️⃣ Normalize / inject logging defaults ---
    logging_cfg = config.get("logging", {})
    level = str(logging_cfg.get("level", "INFO")).upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    if "level" not in logging_cfg:
        logger.warning("No logging.level set; defaulting to INFO.")
        config.setdefault("logging", {}).update({"level": "INFO"})
    elif level not in valid_levels:
        logger.warning(f"Invalid logging.level '{level}'; defaulting to INFO.")
        config["logging"]["level"] = "INFO"
    elif level == "DEBUG" and config.get("allow_debug_in_prod"):
        logger.warning("DEBUG logging is enabled in production via allow_debug_in_prod.")

    config.setdefault("logging", {}).setdefault("format", "%(message)s")

    # --- 6️⃣ Postprocess secrets ---
    process_secrets(config)

    # --- 7️⃣ Inject active profile ---
    config.setdefault("app", {})["profile"] = profile
    logger.info(f"Active profile: {profile}")

    return config





