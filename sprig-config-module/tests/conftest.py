# tests/conftest.py
import os
import logging
import sys
from datetime import datetime
from pathlib import Path
import pytest
import json
import yaml
import shutil


# =====================================================================
# FUTURE ARCHITECTURE IMPORTS
# =====================================================================
# These imports WILL FAIL until we implement the new architecture.
# This is intentional — TDD will drive the implementation.
# ---------------------------------------------------------------------
# Expected future public API of SprigConfig:
#
#   from sprigconfig import (
#       load_config,
#       ConfigLoader,
#       Config,
#       ConfigSingleton,
#       ConfigLoadError,
#   )
#
# load_config() remains for backward compatibility and MUST return a
# Config object (which behaves like a dict but supports dotted keys).
#
# ConfigLoader will implement actual loading + merging logic.
# Config is a mapping wrapper with dotted-key access.
# ConfigSingleton is an optional, thread-safe cached loader.
#
# Until these exist, tests WILL fail.
# ---------------------------------------------------------------------
from sprigconfig import (
    load_config,
    ConfigLoader,     # future
    Config,           # future
    ConfigSingleton,  # future
    ConfigLoadError,
)
from sprigconfig.lazy_secret import LazySecret


# =====================================================================
# CONFIG FIXTURES
# =====================================================================

@pytest.fixture(scope="session")
def patch_config_dir() -> Path:
    """
    Return the default test config directory (tests/config/).
    """
    return Path(__file__).resolve().parent / "config"


CONFIG_DIR = Path(__file__).resolve().parent / "config"


@pytest.fixture
def use_real_config_dir(monkeypatch):
    """
    Set APP_CONFIG_DIR to tests/config.
    This fixture mimics ETL-service-web behavior, where the config
    directory is provided via environment variable.
    """
    config_dir = Path(__file__).parent / "config"
    monkeypatch.setenv("APP_CONFIG_DIR", str(config_dir))
    return config_dir

@pytest.fixture
def full_config_dir(tmp_path_factory):
    """
    Provides a full copy of tests/config inside a temp directory.

    Used by tests that require realistic, multi-file config trees
    (e.g., merge-trace, nested imports, profile overlays).
    """
    # Source: the real config directory in the repo
    src_dir = Path(__file__).parent / "config"
    assert src_dir.exists(), f"Expected test config dir missing: {src_dir}"

    # Destination: isolated copy for the test
    dst_dir = tmp_path_factory.mktemp("config_full")

    # Copy directory tree recursively
    shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)

    return dst_dir

@pytest.fixture
def base_config_dir(tmp_path_factory, monkeypatch):
    """
    DEPRECATED — Kept for backward compatibility.

    Creates a temporary minimal config structure for tests that still
    rely on simple one-file configs.

    NEW tests should use tests/config + use_real_config_dir and rely
    solely on the new ConfigLoader/Config system.
    """
    config_dir = tmp_path_factory.mktemp("config")

    base = {
        "logging": {"level": "INFO", "format": "%(message)s"},
        "app": {"name": "test-app"},
    }

    (config_dir / "application.yml").write_text(yaml.safe_dump(base))

    monkeypatch.setenv("APP_CONFIG_DIR", str(config_dir))
    return config_dir


@pytest.fixture
def load_test_config(tmp_path):
    """
    Integration-style convenience fixture (legacy).
    NEW tests should prefer:
        cfg = ConfigLoader(config_dir, profile).load()
    """
    def _load_test_config(profile=None, config_dir=None):
        if profile is None:
            profile = os.getenv("APP_PROFILE", "dev")
        if config_dir is None:
            config_dir = tmp_path / "config"
            config_dir.mkdir(exist_ok=True)
            (config_dir / "application.yml").write_text("app:\n  name: testapp\n")
        return load_config(profile=profile, config_dir=config_dir)
    return _load_test_config


@pytest.fixture
def load_raw_config():
    """
    For negative tests.
    NEW tests should call ConfigLoader directly.
    """
    def _load_raw_config(profile=None, config_dir=None):
        return load_config(profile=profile, config_dir=config_dir)
    return _load_raw_config


# =====================================================================
# GLOBAL TEST LOGGING
# =====================================================================

@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    """
    Mirror old behavior: detailed timestamped log file + console output.
    """
    log_dir = Path("test_logs")
    log_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logfile = log_dir / f"pytest_{timestamp}.log"

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Reset handlers
    for h in list(root.handlers):
        root.removeHandler(h)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    file_handler = logging.FileHandler(logfile, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    root.addHandler(console_handler)
    root.addHandler(file_handler)

    logging.getLogger(__name__).info("Test logging configured. File: %s", logfile)
    yield
    logging.getLogger(__name__).info("Tests finished. Logs written to %s", logfile)


# =====================================================================
# PYTEST CLI OPTIONS
# =====================================================================

def pytest_addoption(parser):
    # Existing dump-config options
    parser.addoption("--dump-config", action="store_true", help="print merged config")
    parser.addoption("--dump-config-format", choices=["yaml", "json"], default="yaml")
    parser.addoption("--dump-config-secrets", action="store_true",
                     help="resolve LazySecret values before printing")
    parser.addoption("--dump-config-no-redact", action="store_true",
                     help="print plaintext secrets instead of ****")

    # NEW: Write merged config to file
    parser.addoption(
        "--debug-dump",
        action="store",
        default=None,
        help="Write fully merged Config to the given YAML file (safe, redacted).",
    )


def pytest_collection_modifyitems(config, items):
    """Skip crypto tests unless RUN_CRYPTO=true."""
    if os.getenv("RUN_CRYPTO", "").lower() not in ("1", "true", "yes", "on"):
        skip_crypto = pytest.mark.skip(reason="Skipping crypto tests (RUN_CRYPTO not set)")
        for item in items:
            if "crypto" in item.keywords:
                item.add_marker(skip_crypto)


# =====================================================================
# SAFE SERIALIZATION HELPERS
# =====================================================================

def _to_plain(obj, resolve_secrets=False, redact=True):
    """
    Convert Config and LazySecret structures to safe plain dict.
    """
    # LazySecret
    if isinstance(obj, LazySecret):
        if resolve_secrets:
            return "****" if redact else obj.get()
        return "<LazySecret>"

    # New Config object
    if hasattr(obj, "to_dict"):
        obj = obj.to_dict()

    # Dict
    if isinstance(obj, dict):
        return {k: _to_plain(v, resolve_secrets, redact) for k, v in obj.items()}

    # List / tuple
    if isinstance(obj, (list, tuple, set)):
        return [_to_plain(v, resolve_secrets, redact) for v in obj]

    return obj


def dump_config(cfg, *, fmt="yaml", resolve_secrets=False, redact=True):
    """Render config to YAML or JSON cleanly."""
    plain = _to_plain(cfg, resolve_secrets=resolve_secrets, redact=redact)
    return (
        yaml.safe_dump(plain, sort_keys=False)
        if fmt == "yaml"
        else json.dumps(plain, indent=2)
    )


# =====================================================================
# maybe_dump (legacy)
# =====================================================================

@pytest.fixture
def maybe_dump(request):
    """
    Legacy debug print (to stdout).
    """
    def _dump(cfg, *, fmt=None, resolve_secrets=None, redact=None):
        if not request.config.getoption("--dump-config"):
            return ""
        fmt = fmt or request.config.getoption("--dump-config-format")
        resolve_secrets = (
            request.config.getoption("--dump-config-secrets")
            if resolve_secrets is None
            else resolve_secrets
        )
        redact = (
            not request.config.getoption("--dump-config-no-redact")
            if redact is None
            else redact
        )
        txt = dump_config(cfg, fmt=fmt, resolve_secrets=resolve_secrets, redact=redact)
        print(f"\n--- merged config ({request.node.nodeid}) ---\n{txt}\n---")
        return txt
    return _dump


# =====================================================================
# NEW FIXTURE: capture_config (for --debug-dump)
# =====================================================================

@pytest.fixture
def capture_config(request):
    """
    Wrap calls that load Config so that if --debug-dump is provided,
    the fully merged config is written to disk safely.

    Usage:
        cfg = capture_config(lambda: load_config(...))
        OR
        cfg = capture_config(lambda: ConfigLoader(...).load())
    """
    dump_path = request.config.getoption("--debug-dump")
    captured = {}

    def _capture(loader_callable):
        cfg = loader_callable()
        captured["cfg"] = cfg
        return cfg

    yield _capture

    if dump_path and "cfg" in captured:
        plain = _to_plain(captured["cfg"], resolve_secrets=False, redact=True)
        with open(dump_path, "w") as f:
            yaml.safe_dump(plain, f, sort_keys=False)


# =====================================================================
# END OF FILE
# =====================================================================
