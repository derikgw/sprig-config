# sprig-tools/tests/test_cli_sync_pytest.py
import subprocess
import sys
import textwrap
from pathlib import Path


def run_cli(tmp_path, *args):
    """Helper to run sprig-tool CLI in temp directory."""
    cmd = [sys.executable,  "-u", "-m", "sprigtools.cli", *args]
    result = subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True)
    return result.stdout, result.stderr


def make_pyproject(tmp_path, extra_ini_options=None):
    """Create a minimal pyproject.toml with pytest options."""
    ini_options = textwrap.dedent(f"""
    [tool.pytest.ini_options]
    addopts = "-v"
    testpaths = ["tests"]
    pythonpath = ["src"]
    """)
    if extra_ini_options:
        ini_options += extra_ini_options

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(textwrap.dedent(f"""
    [project]
    name = "dummy"
    version = "0.1.0"

    {ini_options}
    """))
    return pyproject


def make_pytest_ini(tmp_path, extra=None):
    """Create a minimal pytest.ini."""
    lines = [
        "[pytest]",
        "addopts = -v",
        "testpaths = tests",
        "pythonpath = src"
    ]
    if extra:
        lines.append(extra)
    pytest_ini = tmp_path / "pytest.ini"
    pytest_ini.write_text("\n".join(lines))
    return pytest_ini


def test_to_ini_preview_and_update(tmp_path):
    pyproject = make_pyproject(tmp_path, extra_ini_options='somevar = "bleh"\n')
    pytest_ini = make_pytest_ini(tmp_path)

    # PREVIEW: Should show somevar diff
    out, err = run_cli(tmp_path, "sync-pytest", "to-ini", "--update")
    assert "bleh" in out
    assert pytest_ini.read_text().find("somevar") != -1


def test_to_toml_preview_and_update(tmp_path):
    pyproject = make_pyproject(tmp_path)
    pytest_ini = make_pytest_ini(tmp_path, extra="somevar = bleh")

    # PREVIEW: Should show missing somevar
    out, err = run_cli(tmp_path, "sync-pytest", "to-toml", "--update")
    assert "bleh" in out
    assert "somevar" in pyproject.read_text()


def test_reqs_to_toml_preview_and_update(tmp_path):
    reqs = tmp_path / "requirements.txt"
    reqs.write_text("pytest==8.4.1\ncolorama==0.4.6\n")
    pyproject = make_pyproject(tmp_path)

    # PREVIEW: Should list packages in dev
    out, err = run_cli(tmp_path, "reqs-to-toml", str(reqs), "--pyproject", str(pyproject))
    assert "pytest>=8.4.1" in out
    assert "colorama>=0.4.6" in out

    # UPDATE: Should modify pyproject.toml
    out, err = run_cli(tmp_path, "reqs-to-toml", str(reqs), "--pyproject", str(pyproject), "--update")
    updated_pyproject = pyproject.read_text()
    assert "pytest>=8.4.1" in updated_pyproject
    assert "colorama>=0.4.6" in updated_pyproject
