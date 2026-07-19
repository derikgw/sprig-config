#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Docker creates named-volume roots as root. Dev Containers runs lifecycle
# commands as the non-root vscode user, so claim only the mounted cache paths.
sudo chown -R "$(id -u):$(id -g)" \
    "${repo_root}/sprig-config-module/.venv" \
    "${repo_root}/sprig-tools/.venv" \
    "${HOME}/.cache/pypoetry"

echo "Installing sprig-config-module dependencies..."
cd "${repo_root}/sprig-config-module"
poetry install --with docs --no-ansi

echo "Installing sprig-tools dependencies..."
cd "${repo_root}/sprig-tools"
poetry install --no-ansi

echo "Dev Container setup complete."
echo "Core tests:  cd sprig-config-module && poetry run pytest"
echo "Tools tests: cd sprig-tools && poetry run pytest"
