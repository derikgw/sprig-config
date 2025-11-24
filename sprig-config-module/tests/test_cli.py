# tests/test_cli.py

import json
import logging
import subprocess
import sys

import pytest


@pytest.fixture(autouse=True)
def disable_logging_handlers():
    """
    Disable global logging handlers inside the subprocess.
    The CLI should run with a clean stdout environment.
    """
    # Save and remove handlers
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    for h in original_handlers:
        root.removeHandler(h)

    yield

    # Restore handlers
    for h in original_handlers:
        root.addHandler(h)

def run_cli(args, cwd):
    """Run the sprigconfig CLI and return (rc, stdout, stderr)."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "sprigconfig.cli"] + args,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = proc.communicate()
    return proc.returncode, stdout, stderr


def test_cli_dump_basic(tmp_path):
    # Write basic config
    (tmp_path / "application.yml").write_text(
        "app:\n  name: test-app\n"
    )

    rc, out, err = run_cli(
        ["dump", "--config-dir", str(tmp_path), "--profile", "dev"],
        cwd=tmp_path,
    )

    assert rc == 0
    assert "app:" in out
    assert "name: test-app" in out


def test_cli_output_file(tmp_path):
    (tmp_path / "application.yml").write_text("app:\n  y: 2\n")

    out_file = tmp_path / "out.yml"

    rc, out, err = run_cli(
        ["dump", "--config-dir", str(tmp_path),
         "--profile", "dev", "--output", str(out_file)],
        cwd=tmp_path,
    )

    assert rc == 0
    assert out_file.exists()
    assert "y: 2" in out_file.read_text()
