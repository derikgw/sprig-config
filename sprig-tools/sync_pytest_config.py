import argparse
import sys
import subprocess
import importlib.util
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        tomllib = None

DEFAULT_PYPROJECT = "pyproject.toml"
DEFAULT_PYTEST_INI = "pytest.ini"

REQUIRED_PACKAGES = {
    "tomli": "Needed to read TOML on Python <3.11",
    "tomli_w": "Needed to write TOML files"
}

def check_dependency(package):
    """Return True if package is installed, else False."""
    return importlib.util.find_spec(package) is not None

def install_dependencies():
    """Install missing dependencies using pip."""
    missing = [pkg for pkg in REQUIRED_PACKAGES if not check_dependency(pkg)]
    if not missing:
        print("✅ All dependencies already installed.")
        return True

    print(f"📦 Installing missing dependencies: {', '.join(missing)}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        print("✅ Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def pyproject_to_ini(pyproject_path, pytest_ini_path):
    """Generate pytest.ini from pyproject.toml"""
    pyproject = Path(pyproject_path)
    pytest_ini = Path(pytest_ini_path)

    if not pyproject.exists():
        sys.exit(f"❌ {pyproject} not found")

    if tomllib is None:
        sys.exit("❌ Missing tomllib/tomli. Run with --install-dependencies.")

    with pyproject.open("rb") as f:
        data = tomllib.load(f)

    pytest_opts = data.get("tool", {}).get("pytest", {}).get("ini_options", {})
    if not pytest_opts:
        sys.exit("❌ No [tool.pytest.ini_options] section found in pyproject.toml")

    lines = ["[pytest]"]
    for key, value in pytest_opts.items():
        if isinstance(value, list):
            value = " ".join(value)
        lines.append(f"{key} = {value}")

    pytest_ini.write_text("\n".join(lines))
    print(f"✅ Generated {pytest_ini} from {pyproject}")

def ini_to_pyproject(pyproject_path, pytest_ini_path):
    """Import pytest.ini into pyproject.toml"""
    if not check_dependency("tomli_w"):
        sys.exit("❌ Missing tomli_w. Run with --install-dependencies.")

    import tomli_w

    pyproject = Path(pyproject_path)
    pytest_ini = Path(pytest_ini_path)

    if not pytest_ini.exists():
        sys.exit(f"❌ {pytest_ini} not found")

    opts = {}
    for line in pytest_ini.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("["):
            continue
        if "=" in line:
            key, value = map(str.strip, line.split("=", 1))
            if " " in value:
                value = value.split()
            opts[key] = value

    py_data = {}
    if pyproject.exists():
        with pyproject.open("rb") as f:
            py_data = tomllib.load(f)

    py_data.setdefault("tool", {}).setdefault("pytest", {})["ini_options"] = opts

    with pyproject.open("wb") as f:
        tomli_w.dump(py_data, f)

    print(f"✅ Updated {pyproject} from {pytest_ini}")

def main():
    parser = argparse.ArgumentParser(
        description="Sync pytest config between pyproject.toml and pytest.ini",
        add_help=False
    )

    parser.add_argument("action", nargs="?", choices=["to-ini", "to-toml", "/?", "=?"],
                        help="Action: to-ini (generate pytest.ini) | to-toml (update pyproject.toml)")

    parser.add_argument("--install-dependencies", action="store_true",
                        help="Install all missing dependencies before running")

    parser.add_argument("--pyproject", default=DEFAULT_PYPROJECT,
                        help=f"Path to pyproject.toml (default: {DEFAULT_PYPROJECT})")

    parser.add_argument("--pytest-ini", default=DEFAULT_PYTEST_INI,
                        help=f"Path to pytest.ini (default: {DEFAULT_PYTEST_INI})")

    parser.add_argument("-h", "--help", action="help",
                        help="Show this help message and exit")

    args = parser.parse_args()

    # If neither action nor flags given → show help
    if not args.action and not args.install_dependencies:
        parser.print_help()
        sys.exit(0)

    # Install dependencies if requested
    if args.install_dependencies:
        if not install_dependencies():
            sys.exit(1)
        # If only installing deps, exit early
        if not args.action:
            sys.exit(0)

    # If action is help-style, show help
    if args.action in ["/?", "=?"]:
        parser.print_help()
        sys.exit(0)

    # Execute actions
    if args.action == "to-ini":
        pyproject_to_ini(args.pyproject, args.pytest_ini)
    elif args.action == "to-toml":
        ini_to_pyproject(args.pyproject, args.pytest_ini)

if __name__ == "__main__":
    main()
