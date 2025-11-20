# sprigconfig/config_loader.py
"""
ConfigLoader: the primary configuration loader for SprigConfig.

Responsibilities:
- Load application.yml
- Load application-<profile>.yml if it exists
- Deep-merge the two
- Recursively process imports directives *literally at their location*
- Delete `imports:` keys after processing
- Detect circular imports
- Expand ${ENV} and ${ENV:default} values before YAML parsing
- Wrap ENC(...) strings as LazySecret
- Produce a final Config object
"""

import os
import re
from pathlib import Path
from typing import Dict, Any

import yaml

from .config import Config
from .lazy_secret import LazySecret
from .exceptions import ConfigLoadError
from .deepmerge import deep_merge


ENV_PATTERN = re.compile(r"\$\{([^}:]+)(?::([^}]+))?\}")


class ConfigLoader:
    """
    Loads configuration from a directory using:
        application.yml
        application-<profile>.yml

    Performs:
        - env var expansion
        - deep merges
        - recursive literal import processing
        - circular import detection
        - LazySecret injection

    Returns:
        Config
    """

    def __init__(self, config_dir: Path, profile: str):
        # Legacy fallback for missing config_dir
        if config_dir is None:
            env_dir = os.getenv("APP_CONFIG_DIR")
            if not env_dir:
                raise ConfigLoadError(
                    "No config_dir provided and APP_CONFIG_DIR not set"
                )
            config_dir = Path(env_dir)

        self.config_dir = Path(config_dir)
        self.profile = profile
        self._seen_imports = set()       # tracks file paths for circular detection

    # ----------------------------------------------------------------------
    # PUBLIC API
    # ----------------------------------------------------------------------

    def load(self) -> Config:
        """Load, merge, import, postprocess, and return a Config."""
        base = self._load_yaml(self.config_dir / "application.yml")

        profile_path = self.config_dir / f"application-{self.profile}.yml"
        profile_data = self._load_yaml(profile_path) if profile_path.exists() else {}

        suppress = (
            base.get("suppress_config_merge_warnings", False)
            or profile_data.get("suppress_config_merge_warnings", False)
        )

        merged = deep_merge(base, profile_data, suppress=suppress)

        # Recursively process imports anywhere in the config tree
        self._apply_imports_recursive(merged, suppress=suppress)

        # Normalize active profile (file profile is ignored)
        merged.setdefault("app", {})["profile"] = self.profile

        # Wrap secrets
        self._inject_secrets(merged)

        return Config(merged)

    # ----------------------------------------------------------------------
    # YAML LOADING + ENV EXPANSION
    # ----------------------------------------------------------------------

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}

        try:
            text = path.read_text(encoding="utf-8-sig")  # BOM-safe
            expanded = self._expand_env(text)
            data = yaml.safe_load(expanded)
            return data if data else {}
        except yaml.YAMLError as e:
            raise ConfigLoadError(f"Invalid YAML in {path}: {e}")

    def _expand_env(self, text: str) -> str:
        def replacer(match):
            var, default = match.groups()
            return os.getenv(var, default if default is not None else match.group(0))

        return ENV_PATTERN.sub(replacer, text)

    # ----------------------------------------------------------------------
    # IMPORT PROCESSING (literal, recursive)
    # ----------------------------------------------------------------------

    def _apply_imports_recursive(self, node: Dict[str, Any], suppress: bool):
        """
        Walk the entire config tree.
        Whenever an `imports:` key is found:
         - resolve each import
         - detect circularity
         - load the imported YAML
         - recursively process its imports first
         - deep-merge imported content *into this exact node*
         - REMOVE `imports:` directive afterwards
        """
        if not isinstance(node, dict):
            return

        # Process imports at this node (if present)
        if "imports" in node:
            imports_list = node.get("imports", [])
            if isinstance(imports_list, list):
                for imp in imports_list:
                    imp_file = (self.config_dir / imp).resolve()

                    # Circular detection
                    if str(imp_file) in self._seen_imports:
                        raise ConfigLoadError(f"Circular import detected: {imp_file}")
                    self._seen_imports.add(str(imp_file))

                    imported = self._load_yaml(imp_file)

                    # Process imports in imported file first
                    self._apply_imports_recursive(imported, suppress=suppress)

                    # Literal deep merge into this node
                    deep_merge(node, imported, suppress=suppress)

            # Remove the directive AFTER processing
            del node["imports"]

        # Recursively walk child dicts
        for key, value in list(node.items()):
            if isinstance(value, dict):
                self._apply_imports_recursive(value, suppress=suppress)
            elif isinstance(value, list):
                # Lists may contain dicts
                for item in value:
                    if isinstance(item, dict):
                        self._apply_imports_recursive(item, suppress=suppress)

    # ----------------------------------------------------------------------
    # SECRET PROCESSING
    # ----------------------------------------------------------------------

    def _inject_secrets(self, data: Dict[str, Any]):
        """Wrap ENC(...) strings in LazySecret recursively."""
        for key, value in list(data.items()):
            if isinstance(value, str) and value.startswith("ENC(") and value.endswith(")"):
                data[key] = LazySecret(value, key=os.getenv("APP_SECRET_KEY"))
            elif isinstance(value, dict):
                self._inject_secrets(value)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str) and item.startswith("ENC(") and item.endswith(")"):
                        value[i] = LazySecret(item, key=os.getenv("APP_SECRET_KEY"))
                    elif isinstance(item, dict):
                        self._inject_secrets(item)
