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
- Inject RC3 metadata:
      sprigconfig._meta.profile
      sprigconfig._meta.sources
- Produce final Config object
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List

import yaml

from .config import Config
from .lazy_secret import LazySecret
from .exceptions import ConfigLoadError
from .deepmerge import deep_merge

# Regex for ${ENV} and ${ENV:default}
ENV_PATTERN = re.compile(r"\$\{([^}:]+)(?::([^}]+))?\}")


class ConfigLoader:
    """
    Loads configuration using:
        application.yml
        application-<profile>.yml

    Performs:
        - env expansion
        - YAML loading
        - deep merges
        - recursive literal import processing
        - circular import detection
        - LazySecret injection
        - RC3 metadata injection (_meta.profile, _meta.sources)

    Returns:
        Config
    """

    def __init__(self, config_dir: Path, profile: str):
        # Legacy fallback for env-based config_dir
        if config_dir is None:
            env_dir = os.getenv("APP_CONFIG_DIR")
            if not env_dir:
                raise ConfigLoadError(
                    "No config_dir provided and APP_CONFIG_DIR not set"
                )
            config_dir = Path(env_dir)

        self.config_dir = Path(config_dir)
        self.profile = profile

        # Circular detection
        self._seen_imports: set[str] = set()

        # Ordered list of loaded YAML files
        self._merge_trace: List[str] = []

    # ======================================================================
    # PUBLIC API
    # ======================================================================

    def load(self) -> Config:
        """Load, merge, process imports, inject metadata and secrets."""
        # 1. Base config
        base = self._load_yaml(self.config_dir / "application.yml")

        # 2. Profile overlay
        profile_path = self.config_dir / f"application-{self.profile}.yml"
        profile_data = (
            self._load_yaml(profile_path) if profile_path.exists() else {}
        )

        # Merge warning suppression
        suppress = (
            base.get("suppress_config_merge_warnings", False)
            or profile_data.get("suppress_config_merge_warnings", False)
        )

        merged = deep_merge(base, profile_data, suppress=suppress)

        # 3. Recursively apply imports anywhere
        self._apply_imports_recursive(merged, suppress=suppress)

        # 4. Normalize active profile (file-defined app.profile is overridden)
        merged.setdefault("app", {})["profile"] = self.profile

        # 5. Inject RC3 metadata
        self._inject_metadata(merged)

        # 6. Wrap all ENC(...) secrets
        self._inject_secrets(merged)

        return Config(merged)

    # ======================================================================
    # YAML LOADING
    # ======================================================================

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}

        resolved = path.resolve()

        # NEW — record every loaded YAML file
        self._merge_trace.append(str(resolved))

        try:
            text = path.read_text(encoding="utf-8-sig")
            expanded = self._expand_env(text)
            data = yaml.safe_load(expanded)
            return data if data else {}
        except yaml.YAMLError as e:
            raise ConfigLoadError(f"Invalid YAML in {path}: {e}")

    def _expand_env(self, text: str) -> str:
        """Replace ${ENV} and ${ENV:default}."""
        def replacer(match):
            var, default = match.groups()
            return os.getenv(var, default if default is not None else match.group(0))

        return ENV_PATTERN.sub(replacer, text)

    # ======================================================================
    # IMPORT PROCESSING
    # ======================================================================

    def _apply_imports_recursive(self, node: Dict[str, Any], suppress: bool):
        """
        Recursively walk the configuration tree.
        Whenever an `imports:` key is found:
            - resolve each import
            - detect circularity
            - record the imported YAML in merge trace
            - load YAML
            - recursively process its imports first
            - deep-merge into current node
        Then remove the `imports:` key.
        """
        if not isinstance(node, dict):
            return

        # Process imports at this node
        if "imports" in node:
            imports_list = node.get("imports", [])

            if isinstance(imports_list, list):
                for imp in imports_list:
                    imp_file = (self.config_dir / imp).resolve()

                    # Circular import detection
                    if str(imp_file) in self._seen_imports:
                        raise ConfigLoadError(f"Circular import detected: {imp_file}")
                    self._seen_imports.add(str(imp_file))

                    # Record BEFORE loading
                    self._merge_trace.append(str(imp_file))

                    imported_yaml = self._load_yaml(imp_file)

                    # Process imports within the imported file first
                    self._apply_imports_recursive(imported_yaml, suppress)

                    # Literal deep merge
                    deep_merge(node, imported_yaml, suppress=suppress)

            # Remove imports directive
            del node["imports"]

        # Recurse children
        for key, value in list(node.items()):
            if isinstance(value, dict):
                self._apply_imports_recursive(value, suppress=suppress)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._apply_imports_recursive(item, suppress=suppress)

    # ======================================================================
    # SECRETS
    # ======================================================================

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

    # ======================================================================
    # METADATA (RC3)
    # ======================================================================

    def _inject_metadata(self, merged: dict):
        """
        Injects:

            sprigconfig:
              _meta:
                profile: <runtime profile>
                sources: [list-of-loaded-yaml-files]

        User-defined sprigconfig._meta.* keys are preserved.
        """
        runtime_profile = self.profile or "default"

        node = merged.setdefault("sprigconfig", {})
        meta = node.setdefault("_meta", {})

        # profile — do not overwrite user-specified
        if "profile" not in meta:
            meta["profile"] = runtime_profile

        # sources — do not overwrite user-specified
        if "sources" not in meta:
            meta["sources"] = list(self._merge_trace)
