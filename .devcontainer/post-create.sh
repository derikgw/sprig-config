#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Docker can create mount targets and their parent directories as root before
# the remoteUser is applied. Claim the project volumes and the full cache tree
# so tools that create their own cache subdirectories do not fail.
sudo chown -R "$(id -u):$(id -g)" \
    "${repo_root}/sprig-config-module/.venv" \
    "${HOME}/.cache"

echo "Installing sprig-config-module dependencies..."
cd "${repo_root}/sprig-config-module"
poetry install --with docs --no-ansi

echo "Dev Container setup complete."
echo "Core tests:  cd sprig-config-module && poetry run pytest"
