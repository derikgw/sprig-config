#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

import configparser
import tomllib

from colorama import Fore, Style, init as colorama_init

from sprigtools import sync_pytest_config
from sprigtools.sync_pytest_config import HelpOnErrorParser

# Initialize colorama
colorama_init(autoreset=True, strip=bool(os.getenv("PYTEST_CURRENT_TEST")))


def find_base_dir():
    cwd = Path.cwd()
    for _ in range(5):  # climb up a few levels
        if (cwd / "sprig-config-module").exists() and (cwd / "sprig-tools").exists():
            return cwd
        cwd = cwd.parent
    return Path.cwd()  # fallback


BASE_DIR = find_base_dir()

PROJECT_PATHS = {
    "module": {
        "reqs": BASE_DIR / "sprig-config-module" / "requirements.txt",
        "pyproject": BASE_DIR / "sprig-config-module" / "pyproject.toml"
    },
    "tools": {
        "reqs": BASE_DIR / "sprig-tools" / "requirements.txt",
        "pyproject": BASE_DIR / "sprig-tools" / "pyproject.toml"
    }
}


def run_pytest_sync(action, update, project_key):
    """Sync pytest configs for a specific project."""
    project_data = PROJECT_PATHS[project_key]
    proj_py_path = Path(project_data["pyproject"])
    proj_ini_path = Path(project_data["reqs"]).parent / "pytest.ini"

    print("\n" + "=" * 60, flush=True)
    print(f"🔄 PROJECT: {Fore.CYAN}{project_key.upper()}{Style.RESET_ALL}", flush=True)
    print("=" * 60, flush=True)

    ini_config = configparser.ConfigParser()
    ini_config.read(proj_ini_path)
    ini_opts = dict(ini_config.items("pytest")) if ini_config.has_section("pytest") else {}

    with open(proj_py_path, "rb") as f:
        data = tomllib.load(f)
    toml_opts = data.get("tool", {}).get("pytest", {}).get("ini_options", {})

    def compare_toml_to_ini():
        diffs_list = []
        for key, value in toml_opts.items():
            toml_value = " ".join(value) if isinstance(value, list) else str(value)
            ini_value = ini_opts.get(key)
            if ini_value != toml_value:
                diffs_list.append(f"{Fore.YELLOW}  {key}: '{ini_value}' → '{toml_value}'{Style.RESET_ALL}")
        for key in set(ini_opts) - set(toml_opts):
            diffs_list.append(f"{Fore.YELLOW}  {key}: present in INI but missing in TOML{Style.RESET_ALL}")
        return diffs_list

    def compare_ini_to_toml():
        diffs_list = []
        for key, value in ini_opts.items():
            ini_value = value.strip()
            toml_value = toml_opts.get(key)
            if isinstance(toml_value, list):
                toml_value = " ".join(toml_value)
            if toml_value != ini_value:
                diffs_list.append(f"{Fore.YELLOW}  {key}: '{toml_value}' → '{ini_value}'{Style.RESET_ALL}")
        for key in set(toml_opts) - set(ini_opts):
            diffs_list.append(f"{Fore.YELLOW}  {key}: present in TOML but missing in INI{Style.RESET_ALL}")
        return diffs_list

    diffs_list = compare_toml_to_ini() if action == "to-ini" else compare_ini_to_toml()
    if diffs_list:
        print(Fore.YELLOW + "[Preview of changes before update]:" + Style.RESET_ALL, flush=True)
        for diff in diffs_list:
            print(diff, flush=True)
    else:
        print(Fore.GREEN + "  No changes detected" + Style.RESET_ALL, flush=True)

    if update and diffs_list:
        print(Fore.GREEN + "Applying changes..." + Style.RESET_ALL, flush=True)
        if action == "to-ini":
            sync_pytest_config.pyproject_to_ini(proj_py_path, proj_ini_path)
        elif action == "to-toml":
            sync_pytest_config.ini_to_pyproject(proj_py_path, proj_ini_path)


def run_reqs_sync(update, project_key=None, reqs_file=None, pyproject_file=None):
    """Sync requirements to TOML for a project or direct file pair."""
    from sprigtools.reqs_to_toml import (
        sync_versions_with_freeze,
        preview_requirements_classification
    )

    if project_key:
        project_data = PROJECT_PATHS[project_key]
        proj_reqs_path = Path(project_data["reqs"])
        proj_py_path = Path(project_data["pyproject"])
    else:
        proj_reqs_path = Path(reqs_file)
        proj_py_path = Path(pyproject_file)

    print("\n" + "=" * 60, flush=True)
    print(f"🔄 PROJECT: {Fore.CYAN}{(project_key or proj_py_path).upper()}{Style.RESET_ALL}", flush=True)
    print("=" * 60, flush=True)

    preview_requirements_classification(proj_reqs_path, proj_py_path)

    if update:
        print(Fore.GREEN + "Applying dependency sync..." + Style.RESET_ALL, flush=True)
        sync_versions_with_freeze(proj_reqs_path, proj_py_path)
        print(Fore.GREEN + f"✅ Synced dependencies in {proj_py_path}", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="Sprig Tools CLI - utilities for SprigConfig",
    )

    subparsers = parser.add_subparsers(dest="command", parser_class=HelpOnErrorParser)

    # ---- sync-pytest ----
    pytest_parser = subparsers.add_parser(
        "sync-pytest",
        help="Sync pytest.ini and pyproject.toml",
        description="Synchronize pytest configuration between pyproject.toml and pytest.ini."
    )
    pytest_parser.add_argument("action", choices=["to-ini", "to-toml"], help="Action to perform")
    pytest_parser.add_argument("--pyproject", default="pyproject.toml", help="Path to pyproject.toml")
    pytest_parser.add_argument("--pytest-ini", default="pytest.ini", help="Path to pytest.ini")
    pytest_parser.add_argument("--install-dependencies", action="store_true", help="Install missing dependencies")
    pytest_parser.add_argument("--sync-all", action="store_true", help="Sync pytest config for all projects in mono-repo")
    pytest_parser.add_argument("--project", choices=PROJECT_PATHS.keys(),
                               help="Shortcut: select mono-repo project (module/tools)")
    pytest_parser.add_argument("--update", action="store_true", help="Write changes (default is preview mode)")

    # ---- reqs-to-toml ----
    reqs_parser = subparsers.add_parser(
        "reqs-to-toml",
        help="Convert/sync requirements.txt to TOML dev deps",
        description="Convert or sync requirements.txt to pyproject.toml [tool.poetry.dev-dependencies] section."
    )
    reqs_parser.add_argument("--sync-all", action="store_true", help="Sync all projects in mono-repo")
    reqs_parser.add_argument("reqs_file", nargs="?", help="Path to requirements.txt (optional if using --project)")
    reqs_parser.add_argument("--pyproject", help="Path to pyproject.toml (optional if using --project)")
    reqs_parser.add_argument("--project", choices=PROJECT_PATHS.keys(),
                             help="Shortcut: select mono-repo project (module/tools)")
    reqs_parser.add_argument("--output", help="Optional output file for TOML section")
    reqs_parser.add_argument("--update", action="store_true",
                             help="Update pyproject.toml dependencies with versions from requirements.txt")

    # Custom validation for reqs-to-toml at parse time
    def validate_reqs_args(args):
        if args.command == "reqs-to-toml":
            if not args.sync_all and not args.project and (not args.reqs_file or not args.pyproject):
                reqs_parser.error("You must specify --project, --sync-all, or both reqs_file and --pyproject")

    args = parser.parse_args()
    validate_reqs_args(args)

    # ---- Command Dispatch ----
    if args.command == "sync-pytest":
        if args.install_dependencies:
            if not sync_pytest_config.install_dependencies():
                print(Fore.RED + "❌ Failed to install dependencies.", flush=True)
                sys.exit(1)

        if args.sync_all:
            for proj in PROJECT_PATHS:
                run_pytest_sync(args.action, args.update, proj)
        elif args.project:
            run_pytest_sync(args.action, args.update, args.project)
        else:
            run_pytest_sync(args.action, args.update, "module")

    elif args.command == "reqs-to-toml":
        if args.sync_all:
            for proj in PROJECT_PATHS:
                run_reqs_sync(args.update, project_key=proj)
        elif args.project:
            run_reqs_sync(args.update, project_key=args.project)
        else:
            run_reqs_sync(args.update, reqs_file=args.reqs_file, pyproject_file=args.pyproject)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
