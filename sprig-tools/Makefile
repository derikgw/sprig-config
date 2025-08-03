.PHONY: help test coverage integration

# Default target
help:
	@echo "Available targets:"
	@echo "  make test         Run all tests"
	@echo "  make coverage     Run all tests with coverage"
	@echo "  make integration  Run only integration tests"

test:
	./scripts/run_pytest.sh

coverage:
	./scripts/run_pytest.sh --coverage

integration:
	./scripts/run_pytest.sh --integration
