#!/bin/bash
# scripts/run_pytest.sh for sprig-config
LOG_DIR="test_logs"
COVERAGE_DIR="coverage_reports"
mkdir -p "$LOG_DIR" "$COVERAGE_DIR"

TIMESTAMP=$(date +'%Y%m%d_%H%M%S')
LOG_FILE="$LOG_DIR/pytest_log_$TIMESTAMP.txt"
HTML_REPORT_DIR="$COVERAGE_DIR/html_$TIMESTAMP"

run_pytest() {
    echo "Running: pytest $*"
    pytest "$@" 2>&1 | tee -a "$LOG_FILE"
}

COVERAGE=false
COVERAGE_GAPS=false
PYTEST_ARGS=()

show_help() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS] [pytest args]

Options:
  --coverage              Run tests with coverage (HTML + terminal summary).
  --coverage-gaps         Run only tests marked with coverage_gaps and generate coverage report.
  --help|-h|/h|/?         Show this help message.
  --help|-h|/h|/? pytest  Show pytest's built-in help.

Examples:
  $(basename "$0") --coverage
  $(basename "$0") --coverage-gaps -k "test_specific_case"
  $(basename "$0") -v tests
  $(basename "$0") tests/test_loader.py::test_loads_base_config
  $(basename "$0") --lf
EOF
}

# Parse args
for arg in "$@"; do
    case "$arg" in
        --coverage)
            COVERAGE=true
            ;;
        --coverage-gaps)
            COVERAGE_GAPS=true
            ;;
        --help|-h|/h|/\?)
            if [[ "$2" == "pytest" ]]; then
                pytest --help
            else
                show_help
            fi
            exit 0
            ;;
        *)
            PYTEST_ARGS+=("$arg")
            ;;
    esac
done

# Logic
if [[ "$COVERAGE" == true ]]; then
    echo "Running tests with coverage..."
    run_pytest --cov=sprigconfig --cov-report=html:"$HTML_REPORT_DIR" --cov-report=term-missing "${PYTEST_ARGS[@]}"

    echo "HTML coverage report generated at: $HTML_REPORT_DIR/index.html"

elif [[ "$COVERAGE_GAPS" == true ]]; then
    echo "Running coverage gap tests..."
    GAP_REPORT_DIR="$COVERAGE_DIR/gaps_$TIMESTAMP"
    run_pytest -m coverage_gaps --cov=sprigconfig --cov-append --cov-report=html:"$GAP_REPORT_DIR" --cov-report=term-missing "${PYTEST_ARGS[@]}"

    echo "HTML coverage gaps report generated at: $GAP_REPORT_DIR/index.html"

else
    echo "Running tests without coverage..."
    run_pytest "${PYTEST_ARGS[@]}"
fi
