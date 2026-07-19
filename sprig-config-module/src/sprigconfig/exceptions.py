# src/sprigconfig/exceptions.py
class ConfigLoadError(Exception):
    """Raised when configuration fails to load or parse."""


class ConfigValidationError(ConfigLoadError):
    """Raised when loaded configuration fails schema validation."""
