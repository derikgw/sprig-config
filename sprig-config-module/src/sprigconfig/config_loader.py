# sprigconfig/config_loader.py
"""
ConfigLoader with full import-trace support.

Responsibilities:
- Load application.<ext> (yml, json, or toml)
- Load application-<profile>.<ext> overlay
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
import tomllib
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml
import json

from .config import Config
from .lazy_secret import LazySecret
from .exceptions import ConfigLoadError
from .deepmerge import deep_merge

ENV_PATTERN = re.compile(r"\$\{([^}:]+)(?::([^}]+))?\}")


class ConfigLoader:
    """
    Loads config files (YAML, JSON, or TOML) from a directory with support for:
      - application.<ext> (base)
      - application-<profile>.<ext> (overlay)
      - recursive literal imports (inheriting parent format)
      - circular detection
      - LazySecret wrapping
      - metadata injection (profile, sources, import_trace)

    Supported formats:
      - YAML (.yml, .yaml)
      - JSON (.json)
      - TOML (.toml)
    """

    def __init__(self, config_dir: Path, profile: str, *, ext: str | None = None):
        self.ext = (
            ext
            or os.getenv("SPRIGCONFIG_FORMAT")
            or "yml"
        ).lstrip(".")

        if config_dir is None:
            env_dir = os.getenv("APP_CONFIG_DIR")
            if not env_dir:
                raise ConfigLoadError(
                    "No config_dir provided and APP_CONFIG_DIR not set"
                )
            config_dir = Path(env_dir)

        self.config_dir = Path(config_dir)
        self.profile = profile

        # All loaded config file paths
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

        Merge order:
          1. Base (application.<ext>)
          2. Base's imports
          3. Profile overlay (application-<profile>.<ext>)
          4. Profile's imports
          5. Nested imports (recursive)
        """
        # --------------------------------------------------
        # 1. Load application.<ext> (root)
        # --------------------------------------------------
        base_file = self.config_dir / f"application.{self.ext}"
        base = self._load_file(base_file)

        root_file = str(base_file.resolve())

        # Record root as first import_trace entry
        self._record_import(
            file=root_file,
            imported_by=None,
            import_key=None,
            depth=0,
        )

        suppress = base.get("suppress_config_merge_warnings", False)

        # --------------------------------------------------
        # 2. Apply base's imports
        # --------------------------------------------------
        self._apply_imports_recursive(
            base,
            parent_file=root_file,
            depth=0,
            suppress=suppress
        )

        # --------------------------------------------------
        # 3. Load profile overlay
        # --------------------------------------------------
        profile_file = self.config_dir / f"application-{self.profile}.{self.ext}"
        profile_file_resolved = str(profile_file.resolve())

        if profile_file.exists():
            profile_data = self._load_file(profile_file)

            # Record profile overlay
            self._record_import(
                file=profile_file_resolved,
                imported_by=root_file,
                import_key=f"application-{self.profile}.{self.ext}",
                depth=1,
            )

            # Update suppress if profile specifies it
            suppress = suppress or profile_data.get("suppress_config_merge_warnings", False)

            # --------------------------------------------------
            # 4. Apply profile's imports
            # --------------------------------------------------
            self._apply_imports_recursive(
                profile_data,
                parent_file=profile_file_resolved,
                depth=1,
                suppress=suppress
            )
        else:
            profile_data = {}

        # --------------------------------------------------
        # 5. Merge base (with imports) + profile (with imports)
        # --------------------------------------------------
        merged = deep_merge(base, profile_data, suppress=suppress)

        # --------------------------------------------------
        # 6. Normalize runtime profile
        # --------------------------------------------------
        merged.setdefault("app", {})["profile"] = self.profile

        # --------------------------------------------------
        # 7. Inject metadata
        # --------------------------------------------------
        self._inject_metadata(merged)

        # --------------------------------------------------
        # 8. Inject LazySecret wrappers
        # --------------------------------------------------
        self._inject_secrets(merged)

        return Config(merged)

    # ======================================================================
    # Config File Loading
    # ======================================================================

    def _resolve_file(self, stem: str) -> Path:
        return self.config_dir / f"{stem}.{self.ext}"

    def _resolve_import(self, import_key: str) -> Path:
        """
        Resolve import path, appending the current file extension if not present.

        If import_key has no extension (no dot in basename), append self.ext.
        This ensures imports use the same format as the parent config file.

        Raises ConfigLoadError if the resolved path is outside config_dir
        (protects against path traversal attacks).
        """
        import_path = Path(import_key)

        # Check if the basename has an extension
        if '.' not in import_path.name:
            # No extension - append the current format's extension
            import_key = f"{import_key}.{self.ext}"

        resolved_path = (self.config_dir / import_key).resolve()
        config_dir_resolved = self.config_dir.resolve()

        # Path traversal protection: ensure resolved path is within config_dir
        try:
            resolved_path.relative_to(config_dir_resolved)
        except ValueError:
            raise ConfigLoadError(
                f"Path traversal detected: import '{import_key}' "
                f"resolves outside config directory '{config_dir_resolved}'"
            )

        return resolved_path

    def _load_file(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}

        resolved = str(path.resolve())
        self._merge_trace.append(resolved)

        try:
            if self.ext == "yml" or self.ext == "yaml":
                text = path.read_text(encoding="utf-8-sig")
                expanded = self._expand_env(text)
                data = yaml.safe_load(expanded)
            elif self.ext == "json":
                text = path.read_text(encoding="utf-8-sig")
                expanded = self._expand_env(text)
                data = json.loads(expanded)
            elif self.ext == "toml":
                # TOML must be parsed as binary, then we do env expansion on the result
                # Read as text for env expansion first
                text = path.read_text(encoding="utf-8-sig")
                expanded = self._expand_env(text)
                # Parse the expanded text as TOML
                data = tomllib.loads(expanded)
            else:
                raise ConfigLoadError(f"Unsupported config format: {self.ext}")
            return data or {}
        except yaml.YAMLError as e:
            raise ConfigLoadError(f"Invalid YAML in {path}: {e}")
        except json.JSONDecodeError as e:
            raise ConfigLoadError(f"Invalid JSON in {path}: {e}")
        except tomllib.TOMLDecodeError as e:
            raise ConfigLoadError(f"Invalid TOML in {path}: {e}")

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
                    imp_file = self._resolve_import(import_key)
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

                    imported_yaml = self._load_file(imp_file)

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
