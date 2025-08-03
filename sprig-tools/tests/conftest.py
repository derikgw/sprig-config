# conftest.py
import pytest
import textwrap

@pytest.fixture
def make_repo(tmp_path):
    """Create a fake repo layout in tmp_path."""
    module_dir = tmp_path / "sprig-config-module"
    tools_dir = tmp_path / "sprig-tools"
    module_dir.mkdir()
    tools_dir.mkdir()

    for project_dir, name in [(module_dir, "sprig-config-module"), (tools_dir, "sprig-tools")]:
        (project_dir / "pyproject.toml").write_text(textwrap.dedent(f"""
        [project]
        name = "{name}"
        version = "0.1.0"

        [tool.pytest.ini_options]
        addopts = "-v"
        testpaths = ["tests"]
        pythonpath = ["src"]
        """))
        (project_dir / "pytest.ini").write_text(textwrap.dedent("""
        [pytest]
        addopts = -v
        testpaths = tests
        pythonpath = src
        """))
        (project_dir / "requirements.txt").write_text("pytest==8.4.1\ncolorama==0.4.6\n")

    return module_dir, tools_dir
