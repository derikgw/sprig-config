# sprig-tools/tests/test_cli_sync_all.py
import subprocess
import sys
import pytest


def run_cli(tmp_path, *args):
    """Helper to run sprig-tool CLI in temp directory."""
    cmd = [sys.executable, "-u", "-m", "sprigtools.cli", *args]
    result = subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True)
    return result.stdout, result.stderr


@pytest.mark.integration
def test_sync_all_mode(make_repo):
    module_path, tools_path = make_repo  # make_repo is already the tuple
    out, err = run_cli(module_path.parent, "sync-pytest", "to-ini", "--sync-all")
    assert "PROJECT: MODULE" in out.upper()
    assert "PROJECT: TOOLS" in out.upper()
