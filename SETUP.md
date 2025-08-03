# SprigConfig Mono-Repo Setup

This repository contains two subprojects:

- **sprig-config-module** – Main runtime library
- **sprig-tools** – Developer helper utilities

Each project maintains its own isolated virtual environment and can be opened in an IDE
with convenience scripts.

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
