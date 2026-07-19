#!/usr/bin/env bash

set -u

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

QUICK_MODE=0
TARGETS=()

usage() {
  cat <<'EOF'
Usage: scripts/dev-env-check.sh [options] [project_dir ...]

Runs a baseline Linux dev environment checklist.

Options:
  --quick            Skip heavier project checks (install/lint/tests)
  --help             Show this help

Examples:
  scripts/dev-env-check.sh
  scripts/dev-env-check.sh --quick
  scripts/dev-env-check.sh sprig-config-module sprig-tools

Optional environment variable:
  DEV_ENV_CI_CMDS    Semicolon-separated commands to run as CI parity smoke checks
                     Example: DEV_ENV_CI_CMDS="poetry run ruff check src;poetry run pytest -q"
EOF
}

log_header() {
  printf "\n${BLUE}== %s ==${NC}\n" "$1"
}

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf "${GREEN}[PASS]${NC} %s\n" "$1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf "${RED}[FAIL]${NC} %s\n" "$1"
}

skip() {
  SKIP_COUNT=$((SKIP_COUNT + 1))
  printf "${YELLOW}[SKIP]${NC} %s\n" "$1"
}

run_check() {
  local label="$1"
  shift
  if "$@" >/tmp/dev-env-check.out 2>/tmp/dev-env-check.err; then
    pass "$label"
  else
    fail "$label"
    if [[ -s /tmp/dev-env-check.err ]]; then
      sed 's/^/  /' /tmp/dev-env-check.err
    elif [[ -s /tmp/dev-env-check.out ]]; then
      sed 's/^/  /' /tmp/dev-env-check.out
    fi
  fi
}

check_cmd_exists() {
  command -v "$1" >/dev/null 2>&1
}

check_gh_auth_status() {
  gh auth status >/tmp/dev-env-check.out 2>/tmp/dev-env-check.err
}

check_git_config_value() {
  local key="$1"
  local val
  val="$(git config --get "$key" 2>/dev/null || true)"
  [[ -n "$val" ]]
}

check_env_present() {
  local var_name="$1"
  [[ -n "${!var_name:-}" ]]
}

discover_projects() {
  local found=()

  if [[ -f "pyproject.toml" ]]; then
    found+=(".")
  fi

  while IFS= read -r path; do
    local dir
    dir="$(dirname "$path")"
    if [[ "$dir" != "." ]]; then
      found+=("$dir")
    fi
  done < <(find . -mindepth 2 -maxdepth 2 -name pyproject.toml | sort)

  printf '%s\n' "${found[@]}" | awk 'NF && !seen[$0]++'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --quick)
      QUICK_MODE=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      TARGETS+=("$1")
      shift
      ;;
  esac
done

log_header "Global Tooling"
run_check "GitHub CLI installed (gh --version)" check_cmd_exists gh
run_check "GitHub CLI authenticated (gh auth status)" check_gh_auth_status
run_check "Git identity configured (user.name)" check_git_config_value user.name
run_check "Git identity configured (user.email)" check_git_config_value user.email
run_check "Python available (python3 --version)" check_cmd_exists python3
run_check "Poetry available (poetry --version)" check_cmd_exists poetry

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  mapfile -t TARGETS < <(discover_projects)
fi

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  skip "No pyproject.toml projects found; skipping project checks"
else
  for project_dir in "${TARGETS[@]}"; do
    log_header "Project: ${project_dir}"

    if [[ ! -d "$project_dir" ]]; then
      fail "Project directory not found: ${project_dir}"
      continue
    fi

    if [[ ! -f "$project_dir/pyproject.toml" ]]; then
      skip "No pyproject.toml in ${project_dir}; skipping"
      continue
    fi

    if [[ "$QUICK_MODE" -eq 1 ]]; then
      skip "Quick mode enabled; skipped poetry install"
      skip "Quick mode enabled; skipped ruff check"
      skip "Quick mode enabled; skipped pytest"
    else
      run_check "Dependencies install in ${project_dir}" bash -lc "cd '$project_dir' && poetry install --no-interaction"
      run_check "Lint in ${project_dir} (ruff check .)" bash -lc "cd '$project_dir' && poetry run ruff check ."
      run_check "Tests in ${project_dir} (pytest -q)" bash -lc "cd '$project_dir' && poetry run pytest -q"
    fi

    if [[ "$project_dir" == *"sprig-config-module"* ]]; then
      if check_env_present APP_PROFILE; then
        pass "APP_PROFILE is set for sprig-config-module"
      else
        skip "APP_PROFILE not set (runtime default is usually dev)"
      fi
      if check_env_present APP_SECRET_KEY; then
        pass "APP_SECRET_KEY is set for sprig-config-module"
      else
        skip "APP_SECRET_KEY not set (required only for crypto/secret flows)"
      fi
    fi
  done
fi

log_header "CI Parity"
if [[ -n "${DEV_ENV_CI_CMDS:-}" ]]; then
  IFS=';' read -r -a ci_cmds <<< "${DEV_ENV_CI_CMDS}"
  for cmd in "${ci_cmds[@]}"; do
    cleaned="$(echo "$cmd" | xargs)"
    [[ -z "$cleaned" ]] && continue
    run_check "CI parity command: $cleaned" bash -lc "$cleaned"
  done
else
  skip "Set DEV_ENV_CI_CMDS to run custom CI parity smoke commands"
fi

printf "\n${BLUE}Summary:${NC} %s pass, %s fail, %s skip\n" "$PASS_COUNT" "$FAIL_COUNT" "$SKIP_COUNT"

if [[ "$FAIL_COUNT" -gt 0 ]]; then
  exit 1
fi

exit 0
