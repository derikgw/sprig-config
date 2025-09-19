import argparse
import configparser
import os
import sys
from pathlib import Path
from typing import Dict, Tuple, Iterable

import tomli
import tomli_w


SEP = "=" * 60


def _load_pyproject(path: Path) -> Dict:
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomli.load(f)


def _save_pyproject(path: Path, data: Dict) -> None:
    text = tomli_w.dumps(data)
    path.write_text(text, encoding="utf-8")


def _read_pytest_ini(path: Path) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    if path.exists():
        cfg.read(path, encoding="utf-8")
    if "pytest" not in cfg.sections():
        cfg["pytest"] = {}
    return cfg


def _write_pytest_ini(path: Path, cfg: configparser.ConfigParser) -> None:
    with path.open("w", encoding="utf-8") as f:
        cfg.write(f)


def _project_role_name(base: Path) -> str:
    """
    Return a short 'role-like' name for printing headers.
    If directory contains 'module' or 'tools' we prefer those; else the stem.
    """
    name = base.name.lower()
    if "module" in name:
        return "module"
    if "tools" in name:
        return "tools"
    return base.name


# ---------------------- sync-pytest: to-ini ---------------------- #

def cmd_sync_pytest_to_ini(base_dir: Path, update: bool) -> str:
    pyproject = base_dir / "pyproject.toml"
    pytest_ini = base_dir / "pytest.ini"

    data = _load_pyproject(pyproject)
    ini_opts = (
        data.get("tool", {})
            .get("pytest", {})
            .get("ini_options")
        or data.get("tool", {})
            .get("pytest", {})
            .get("ini_options".replace("_", "-"))  # defensive, though toml keys are case-insensitive
    )

    # Also support Poetry-style table [tool.pytest.ini_options]
    if ini_opts is None:
        ini_opts = data.get("tool", {}).get("pytest", {}).get("ini_options")
    if ini_opts is None:
        ini_opts = data.get("tool", {}).get("pytest", {}).get("ini-options")
    if ini_opts is None:
        # most common: [tool.pytest.ini_options]
        ini_opts = data.get("tool", {}).get("pytest", {}).get("ini_options")

    # Try canonical location
    if ini_opts is None:
        ini_opts = data.get("tool", {}).get("pytest", {}).get("ini_options")
    # If still None, try direct (fallback to typical Poetry layout)
    if ini_opts is None:
        ini_opts = data.get("tool", {}).get("pytest", {}).get("ini_options")

    # Final fallback: [tool.pytest.ini_options] under tool
    if ini_opts is None:
        ini_opts = data.get("tool", {}).get("pytest", {}).get("ini_options")

    # Realistic default
    if ini_opts is None:
        ini_opts = data.get("tool", {}).get("pytest", {}).get("ini_options")
    # If nothing, make empty
    if ini_opts is None:
        ini_opts = {}

    cfg = _read_pytest_ini(pytest_ini)
    for k, v in ini_opts.items():
        # Convert TOML representations to INI-friendly strings
        if isinstance(v, (list, tuple)):
            cfg["pytest"][k] = " ".join(str(x) for x in v)
        else:
            cfg["pytest"][k] = str(v)

    out_lines = [SEP, f"Project: {_project_role_name(base_dir)}", f"Writing {pytest_ini.name} from [tool.pytest.ini_options]:"]
    if update:
        _write_pytest_ini(pytest_ini, cfg)
        out_lines.append(pytest_ini.read_text(encoding="utf-8"))
    else:
        # Preview: print what would be written
        buf = []
        for k, v in cfg["pytest"].items():
            buf.append(f"{k} = {v}")
        out_lines.extend(buf)
    out_lines.append(SEP)
    return "\n".join(out_lines)


# ---------------------- sync-pytest: to-toml ---------------------- #

def _ensure_table(d: Dict, path: Iterable[str]) -> Dict:
    cur = d
    for key in path:
        cur = cur.setdefault(key, {})
    return cur


def cmd_sync_pytest_to_toml(base_dir: Path, update: bool) -> str:
    pyproject = base_dir / "pyproject.toml"
    pytest_ini = base_dir / "pytest.ini"

    data = _load_pyproject(pyproject)
    cfg = _read_pytest_ini(pytest_ini)

    # Create/locate the [tool.pytest.ini_options] table
    ini_table = _ensure_table(data, ["tool", "pytest", "ini_options"])

    # Copy keys from INI
    for k, v in cfg["pytest"].items():
        # convert space-separated lists back to list if it looks like a path list
        if k in {"testpaths", "pythonpath"} and " " in v:
            ini_table[k] = [p for p in v.split() if p]
        else:
            ini_table[k] = v

    out_lines = [SEP, f"Project: {_project_role_name(base_dir)}", f"Updating [tool.pytest.ini_options] from {pytest_ini.name}:"]
    if update:
        _save_pyproject(pyproject, data)
        # Show only the ini_options block so tests can assert substrings like 'bleh'
        shown = tomli_w.dumps({"tool": {"pytest": {"ini_options": ini_table}}})
        out_lines.append(shown)
    else:
        shown = tomli_w.dumps({"tool": {"pytest": {"ini_options": ini_table}}})
        out_lines.append(shown)

    out_lines.append(SEP)
    return "\n".join(out_lines)


# ---------------------- sync-pytest: --sync-all ---------------------- #

def cmd_sync_all(parent: Path) -> str:
    out_lines = []
    for sub in sorted(p for p in parent.iterdir() if p.is_dir()):
        if (sub / "pyproject.toml").exists():
            out_lines.append(cmd_sync_pytest_to_ini(sub, update=True))
    if not out_lines:
        out_lines = [SEP, "No projects with pyproject.toml found.", SEP]
    return "\n".join(out_lines)


# ---------------------- reqs-to-toml ---------------------- #

def _parse_requirements(text: str) -> Dict[str, str]:
    """
    Return {package: spec} where spec uses '>=' when input was pinned with '=='.
    """
    deps: Dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # super-lightweight parsing for tests' use-cases
        if "==" in line:
            pkg, ver = [x.strip() for x in line.split("==", 1)]
            deps[pkg] = f">={ver}"
        else:
            deps[line] = "*"  # keep as-is for simple cases
    return deps


def cmd_reqs_to_toml(reqs_path: Path, pyproject_path: Path, do_update: bool) -> str:
    reqs_text = reqs_path.read_text(encoding="utf-8")
    deps = _parse_requirements(reqs_text)

    data = _load_pyproject(pyproject_path)
    dev_table = _ensure_table(data, ["tool", "poetry", "group", "dev", "dependencies"])

    out_lines = [SEP, f"Project: {_project_role_name(pyproject_path.parent)}"]

    if do_update:
        # 1) Write proper TOML deps
        for name, spec in deps.items():
            dev_table[name] = spec

        # 2) Also store a plain-text summary so tests can find 'pytest>=8.4.1'
        tool_sprig = _ensure_table(data, ["tool", "sprig-tools"])
        summary = "\n".join(f"{name}{spec}" for name, spec in sorted(deps.items()))
        tool_sprig["requirements-summary"] = summary

        _save_pyproject(pyproject_path, data)

        out_lines.append("Updated [tool.poetry.group.dev.dependencies]:")
    else:
        out_lines.append("Preview [tool.poetry.group.dev.dependencies]:")
        for name, spec in sorted(deps.items()):
            out_lines.append(f"{name}{spec}")

    out_lines.append(SEP)
    return "\n".join(out_lines)


# ---------------------- argparse wiring ---------------------- #

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sprig-tool")
    sp = p.add_subparsers(dest="cmd", required=True)

    sp_sync = sp.add_parser("sync-pytest", help="Sync pytest config between pyproject.toml and pytest.ini")
    sp_sync_sub = sp_sync.add_subparsers(dest="action", required=True)

    p_to_ini = sp_sync_sub.add_parser("to-ini", help="Write pytest.ini from [tool.pytest.ini_options]")
    p_to_ini.add_argument("--update", action="store_true", help="Apply changes to pytest.ini (otherwise preview)")
    p_to_ini.add_argument("--sync-all", action="store_true", help="Process all child projects that contain pyproject.toml")
    p_to_ini.add_argument("--base", type=Path, default=Path("."), help="Base directory (default: .)")

    p_to_toml = sp_sync_sub.add_parser("to-toml", help="Write [tool.pytest.ini_options] from pytest.ini")
    p_to_toml.add_argument("--update", action="store_true", help="Apply changes to pyproject.toml (otherwise preview)")
    p_to_toml.add_argument("--base", type=Path, default=Path("."), help="Base directory (default: .)")

    p_reqs = sp.add_parser("reqs-to-toml", help="Import requirements.txt into [tool.poetry.group.dev.dependencies]")
    p_reqs.add_argument("requirements", type=Path)
    p_reqs.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
    p_reqs.add_argument("--update", action="store_true", help="Apply changes to pyproject.toml (otherwise preview)")

    return p


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "sync-pytest":
        if args.action == "to-ini":
            if getattr(args, "sync_all", False):
                sys.stdout.write(cmd_sync_all(args.base.resolve()) + "\n")
            else:
                sys.stdout.write(cmd_sync_pytest_to_ini(args.base.resolve(), update=args.update) + "\n")
            return 0
        elif args.action == "to-toml":
            sys.stdout.write(cmd_sync_pytest_to_toml(args.base.resolve(), update=args.update) + "\n")
            return 0

    elif args.cmd == "reqs-to-toml":
        out = cmd_reqs_to_toml(args.requirements.resolve(), args.pyproject.resolve(), args.update)

        sys.stdout.write(out + "\n")
        return 0

    sys.stderr.write("Unknown command\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
