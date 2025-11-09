# src/sprigconfig/__init__.py
from .loader import load_config, deep_merge, ConfigLoadError

__all__ = ["load_config", "deep_merge", "ConfigLoadError"]
