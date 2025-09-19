# tests/conftest.py
import logging
import sys
from datetime import datetime
from pathlib import Path
import pytest

import json, yaml
from sprigconfig.lazy_secret import LazySecret

@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    """
    Global fixture for test logging.
    - Creates test_logs dir.
    - Writes all logs to a timestamped file.
    - Still prints to console.
    """
    log_dir = Path("test_logs")
    log_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logfile = log_dir / f"pytest_{timestamp}.log"

    # Root logger config
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Clear old handlers (pytest may have added one)
    for h in list(root.handlers):
        root.removeHandler(h)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    console_handler.setFormatter(console_fmt)

    # File handler
    file_handler = logging.FileHandler(logfile, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    file_handler.setFormatter(file_fmt)

    root.addHandler(console_handler)
    root.addHandler(file_handler)

    # Announce
    logging.getLogger(__name__).info("Test logging configured. File: %s", logfile)

    yield

    logging.getLogger(__name__).info("Tests finished. Logs written to %s", logfile)

def pytest_addoption(parser):
    parser.addoption("--dump-config", action="store_true", help="print merged config")
    parser.addoption("--dump-config-format", choices=["yaml", "json"], default="yaml")
    parser.addoption("--dump-config-secrets", action="store_true",
                     help="resolve LazySecret values before printing")
    parser.addoption("--dump-config-no-redact", action="store_true",
                     help="when resolving secrets, print plaintext instead of ****")


@pytest.fixture
def maybe_dump(request):
    def _dump(cfg, *, fmt=None, resolve_secrets=None, redact=None):
        if not request.config.getoption("--dump-config"):
            return ""
        fmt = fmt or request.config.getoption("--dump-config-format")
        if resolve_secrets is None:
            resolve_secrets = request.config.getoption("--dump-config-secrets")
        if redact is None:
            # redact unless explicitly told not to
            redact = not request.config.getoption("--dump-config-no-redact")

        txt = dump_config(cfg, fmt=fmt, resolve_secrets=resolve_secrets, redact=redact)
        print(f"\n--- merged config ({request.node.nodeid}) ---\n{txt}\n---")
        return txt
    return _dump

def _to_plain(obj, resolve_secrets=False, redact=True):
    if isinstance(obj, LazySecret):
        if resolve_secrets:
            return "****" if redact else obj.get()
        return "<LazySecret>"
    if isinstance(obj, dict):
        return {k: _to_plain(v, resolve_secrets, redact) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_plain(v, resolve_secrets, redact) for v in obj]
    return obj

def dump_config(cfg, *, fmt="yaml", resolve_secrets=False, redact=True):
    plain = _to_plain(cfg, resolve_secrets=resolve_secrets, redact=redact)
    return yaml.safe_dump(plain, sort_keys=False) if fmt == "yaml" else json.dumps(plain, indent=2)
