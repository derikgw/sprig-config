# SprigConfig Mono-Repo Setup

This repository contains two subprojects:

- **sprig-config-module** – Main runtime library
- **sprig-tools** – Developer helper utilities

Each project maintains its own isolated virtual environment and can be opened in an IDE
with convenience scripts.

---

## VS Code Dev Container

Prerequisites:

- Docker Desktop for Mac is running.
- The VS Code **Dev Containers** extension is installed.

Open the repository root in VS Code, open the Command Palette, and select
**Dev Containers: Reopen in Container**. The first build:

1. creates a Python 3.11 development container;
2. installs Poetry 2.3.1;
3. installs `sprig-config-module` with its documentation dependencies;
4. installs `sprig-tools`;
5. configures VS Code to use the core module's container interpreter.

Each project keeps its own `.venv`. Those directories and Poetry's download
cache are Docker volumes, so Linux environments do not collide with virtual
environments created on macOS and survive container rebuilds.

Run project commands from their respective directories:

```bash
cd sprig-config-module
poetry run pytest
poetry run ruff check src tests
poetry run mkdocs build --strict

cd ../sprig-tools
poetry run pytest
```

Use **Dev Containers: Rebuild Container** after changing files under
`.devcontainer/`. Use **Dev Containers: Rebuild Container Without Cache** when
the base image or Poetry installation needs to be recreated from scratch.

---

## Launching IDEs

### `open-module.sh`
Launches the `sprig-config-module` project in VS Code (default) or PyCharm.

```bash
./open-module.sh           # Opens VS Code in sprig-config-module
./open-module.sh pycharm   # Opens PyCharm in sprig-config-module
```

- **VS Code** will open `sprig-config-module.code-workspace` (if present).
- **PyCharm** will open the project folder and use `.venv` interpreter.

---

### `open-tools.sh`
Launches the `sprig-tools` project in VS Code (default) or PyCharm.

```bash
./open-tools.sh            # Opens VS Code in sprig-tools
./open-tools.sh pycharm    # Opens PyCharm in sprig-tools
```

- **VS Code** will open `sprig-tools.code-workspace` (if present).
- **PyCharm** will open the project folder and use `.venv` interpreter.

---

## Recommended IDE Settings

### VS Code
- Use `Python: Select Interpreter` to set interpreter to `${workspaceFolder}/.venv`.
- Save a `.code-workspace` in each project folder for extra folders/settings.

### PyCharm
- `Settings > Project > Python Interpreter` → set interpreter to project `.venv`.
- Change `File > Settings > Project Opening` to `New Window` for multi-window workflows.

---

## Why Workspaces and `.idea` Are Not Versioned
- IDE config files (`.code-workspace`, `.idea`) are **not committed** to keep repo clean.
- Setup instructions ensure any developer can recreate these with minimal steps.

---

## Creating VS Code Workspaces

### sprig-config-module
1. Open VS Code in `sprig-config-module`.
2. `File > Add Folder to Workspace` if you want more folders.
3. `File > Save Workspace As...` → save as `sprig-config-module.code-workspace` in project folder.

### sprig-tools
1. Open VS Code in `sprig-tools`.
2. `File > Add Folder to Workspace` if you want more folders.
3. `File > Save Workspace As...` → save as `sprig-tools.code-workspace` in project folder.
