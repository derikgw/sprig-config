import tomllib
import tomli_w
from pathlib import Path


def load_pyproject(pyproject_path: Path):
    with pyproject_path.open("rb") as f:
        return tomllib.load(f)


def write_pyproject(pyproject_path: Path, data: dict):
    with pyproject_path.open("wb") as f:
        tomli_w.dump(data, f)


def sync_versions_with_freeze(req_file: Path, pyproject_path: Path = Path("pyproject.toml")):
    data = load_pyproject(pyproject_path)

    # Ensure keys exist
    data.setdefault("project", {})
    data["project"].setdefault("dependencies", [])
    data["project"].setdefault("optional-dependencies", {})
    data["project"]["optional-dependencies"].setdefault("dev", [])

    # Map for fast lookup
    deps = {d.split(">=")[0].split("==")[0]: d for d in data["project"]["dependencies"]}
    dev_deps = {d.split(">=")[0].split("==")[0]: d for d in data["project"]["optional-dependencies"]["dev"]}

    # Process requirements.txt
    with req_file.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-e ") or "git+" in line:
                continue
            pkg, ver = line.split("==", 1)
            pkg_entry = f"{pkg}>={ver}"

            if pkg in deps:
                deps[pkg] = pkg_entry
            elif pkg in dev_deps:
                dev_deps[pkg] = pkg_entry
            else:
                dev_deps[pkg] = pkg_entry

    # Save back to data
    data["project"]["dependencies"] = sorted(deps.values(), key=str.lower)
    data["project"]["optional-dependencies"]["dev"] = sorted(dev_deps.values(), key=str.lower)

    write_pyproject(pyproject_path, data)
    print(f"✅ Synced dependencies in {pyproject_path}")


def convert_requirements_to_toml(req_file: Path) -> str:
    """Old behavior (still available for --output)"""
    with req_file.open() as f:
        converted = []
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-e ") or "git+" in line:
                continue
            if "==" in line:
                pkg, ver = line.split("==", 1)
                converted.append(f'"{pkg}>={ver}"')
            else:
                converted.append(f'"{line}"')
    toml_list = ",\n    ".join(converted)
    return f"dev = [\n    {toml_list}\n]"


def preview_requirements_classification(req_file: Path, pyproject_path: Path = Path("pyproject.toml")):
    data = load_pyproject(pyproject_path)

    deps = {d.split(">=")[0]: d for d in data.get("project", {}).get("dependencies", [])}
    dev_deps = {d.split(">=")[0]: d for d in data.get("project", {}).get("optional-dependencies", {}).get("dev", [])}

    new_dev = {}
    updated_deps = {}
    updated_dev = {}

    with req_file.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-e ") or "git+" in line:
                continue
            pkg, ver = line.split("==", 1)
            pkg_entry = f"{pkg}>={ver}"

            if pkg in deps:
                updated_deps[pkg] = pkg_entry
            elif pkg in dev_deps:
                updated_dev[pkg] = pkg_entry
            else:
                new_dev[pkg] = pkg_entry

    print("[project.dependencies]")
    for v in sorted(updated_deps.values(), key=str.lower):
        print(f"    {v}")

    print("\n[project.optional-dependencies].dev")
    for v in sorted(updated_dev.values(), key=str.lower):
        print(f"    {v}")

    if new_dev:
        print("\nWould add to dev:")
        for v in sorted(new_dev.values(), key=str.lower):
            print(f"    {v}")
