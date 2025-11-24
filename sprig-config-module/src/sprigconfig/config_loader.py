# sprigconfig/config_loader.py
"""
ConfigLoader with full import-trace support.

Responsibilities:
- Load application.yml
- Load application-<profile>.yml overlay
- Expand ${ENV} and ${ENV:default}
- Perform deep merges
- Process recursive literal imports
- Detect circular imports
- Wrap ENC(...) values as LazySecret
- Inject metadata:
      sprigconfig._meta.profile
      sprigconfig._meta.sources
      sprigconfig._meta.import_trace
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

from .config import Config
from .lazy_secret import LazySecret
from .exceptions import ConfigLoadError
from .deepmerge import deep_merge

ENV_PATTERN = re.compile(r"\$\{([^}:]+)(?::([^}]+))?\}")


class ConfigLoader:
    """
    Loads YAML configs from a directory with support for:
      - application.yml (base)
      - application-<profile>.yml (overlay)
      - recursive literal imports
      - circular detection
      - LazySecret wrapping
      - metadata injection (profile, sources, import_trace)
    """

    def __init__(self, config_dir: Path, profile: str):
        if config_dir is None:
            env_dir = os.getenv("APP_CONFIG_DIR")
            if not env_dir:
                raise ConfigLoadError(
                    "No config_dir provided and APP_CONFIG_DIR not set"
                )
            config_dir = Path(env_dir)

        self.config_dir = Path(config_dir)
        self.profile = profile

        # All loaded YAML file paths
        self._merge_trace: List[str] = []

        # import_trace structured events
        self._import_trace: List[dict] = []

        # Detect cycles
        self._seen_imports: set[str] = set()

        # Monotonic order counter
        self._order = 0

    # ======================================================================
    # PUBLIC API
    # ======================================================================

    def load(self) -> Config:
        """
        Load, merge, process imports, inject metadata, wrap secrets.
        """
        # --------------------------------------------------
        # 1. Load application.yml (root)
        # --------------------------------------------------
        base_file = self.config_dir / "application.yml"
        base = self._load_yaml(base_file)

        root_file = str(base_file.resolve())

        # Record root as first import_trace entry
        self._record_import(
            file=root_file,
            imported_by=None,
            import_key=None,
            depth=0,
        )

        # --------------------------------------------------
        # 2. Load profile overlay *immediately after base*
        # --------------------------------------------------
        profile_file = self.config_dir / f"application-{self.profile}.yml"
        profile_file_resolved = str(profile_file.resolve())

        if profile_file.exists():
            profile_data = self._load_yaml(profile_file)

            # Record profile overlay as imported by root
            self._record_import(
                file=profile_file_resolved,
                imported_by=root_file,
                import_key=f"application-{self.profile}.yml",
                depth=1,
            )
        else:
            profile_data = {}

        suppress = (
            base.get("suppress_config_merge_warnings", False)
            or profile_data.get("suppress_config_merge_warnings", False)
        )

        merged = deep_merge(base, profile_data, suppress=suppress)

        # --------------------------------------------------
        # 3. Apply imports recursively
        # --------------------------------------------------
        self._apply_imports_recursive(
            merged,
            parent_file=root_file,
            depth=0,
            suppress=suppress
        )

        # --------------------------------------------------
        # 4. Normalize runtime profile
        # --------------------------------------------------
        merged.setdefault("app", {})["profile"] = self.profile

        # --------------------------------------------------
        # 5. Inject metadata
        # --------------------------------------------------
        self._inject_metadata(merged)

        # --------------------------------------------------
        # 6. Inject LazySecret wrappers
        # --------------------------------------------------
        self._inject_secrets(merged)

        return Config(merged)

    # ======================================================================
    # YAML LOADING
    # ======================================================================

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}

        resolved = str(path.resolve())
        self._merge_trace.append(resolved)

        try:
            text = path.read_text(encoding="utf-8-sig")
            expanded = self._expand_env(text)
            data = yaml.safe_load(expanded)
            return data or {}
        except yaml.YAMLError as e:
            raise ConfigLoadError(f"Invalid YAML in {path}: {e}")

    def _expand_env(self, text: str) -> str:
        def replacer(match):
            var, default = match.groups()
            return os.getenv(var, default if default is not None else match.group(0))

        return ENV_PATTERN.sub(replacer, text)

    # ======================================================================
    # IMPORT PROCESSING + TRACE
    # ======================================================================

    def _record_import(
        self,
        *,
        file: str,
        imported_by: Optional[str],
        import_key: Optional[str],
        depth: int
    ):
        self._import_trace.append(
            {
                "file": file,
                "imported_by": imported_by,
                "import_key": import_key,
                "depth": depth,
                "order": self._order,
            }
        )
        self._order += 1

    def _apply_imports_recursive(
        self,
        node: Dict[str, Any],
        *,
        parent_file: str,
        depth: int,
        suppress: bool
    ):
        """
        Walk the tree for `imports:` anywhere.
        Maintain correct:
            - imported_by
            - depth
            - order
            - cycle detection
        """
        if not isinstance(node, dict):
            return

        # --------------------------------------------------
        # Process imports on this node
        # --------------------------------------------------
        if "imports" in node:
            imports_list = node.get("imports", [])

            if isinstance(imports_list, list):
                for import_key in imports_list:
                    imp_file = (self.config_dir / import_key).resolve()
                    imp_str = str(imp_file)

                    # Cycle detection
                    if imp_str in self._seen_imports:
                        raise ConfigLoadError(f"Circular import detected: {imp_file}")
                    self._seen_imports.add(imp_str)

                    # Record BEFORE loading
                    self._record_import(
                        file=imp_str,
                        imported_by=parent_file,
                        import_key=import_key,
                        depth=depth + 1,
                    )

                    imported_yaml = self._load_yaml(imp_file)

                    # Recurse using this file as new parent
                    self._apply_imports_recursive(
                        imported_yaml,
                        parent_file=imp_str,
                        depth=depth + 1,
                        suppress=suppress
                    )

                    # Merge into current node
                    deep_merge(node, imported_yaml, suppress=suppress)

            # Remove the directive so it's not in final config
            del node["imports"]

        # --------------------------------------------------
        # Recurse child structures
        # --------------------------------------------------
        for key, value in list(node.items()):
            if isinstance(value, dict):
                self._apply_imports_recursive(
                    value,
                    parent_file=parent_file,
                    depth=depth,
                    suppress=suppress
                )
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._apply_imports_recursive(
                            item,
                            parent_file=parent_file,
                            depth=depth,
                            suppress=suppress
                        )

    # ======================================================================
    # SECRETS
    # ======================================================================

    def _inject_secrets(self, data: Dict[str, Any]):
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
    # METADATA
    # ======================================================================

    def _inject_metadata(self, merged: dict):
        runtime_profile = self.profile or "default"

        node = merged.setdefault("sprigconfig", {})
        meta = node.setdefault("_meta", {})

        # Don't overwrite user-defined
        meta.setdefault("profile", runtime_profile)
        meta.setdefault("sources", list(self._merge_trace))
        meta.setdefault("import_trace", list(self._import_trace))
