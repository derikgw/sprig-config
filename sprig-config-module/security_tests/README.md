# SprigConfig Security Tests

Security-focused tests are kept in this directory rather than mixed into the
functional API suites under `tests/`. They check explicit confidentiality,
integrity, and filesystem-boundary properties. A passing test is evidence for
the exercised input and output path, not a guarantee against every possible
failure mode.

## Test modules

| Module | Scope |
|---|---|
| [`test_guarantees.py`](./test_guarantees.py) | Property-based checks for secret serialization/reveal behavior, singleton secret preservation, and import path boundaries, including symlink escapes and encoded lookalikes. |
| [`test_known_findings.py`](./test_known_findings.py) | Issue #41 regressions, including synthetic-marker checks for parser, CLI, binding, and instantiation diagnostics. Open findings remain strict expected failures by default. |
| [`test_runner.py`](./test_runner.py) | Tests that scanner and dependency-audit gates distinguish clean results, findings, and incomplete or failed scans. |

## Run

From `sprig-config-module/`:

```bash
poetry run pytest security_tests
poetry run python scripts/security_check.py --only tests
```

`security_tests/` is intentionally outside pytest's default `testpaths`, so
ordinary `poetry run pytest` does not collect it. The security check runs it
explicitly. To make unresolved issue #41 cases fail instead of remain expected
failures, run:

```bash
poetry run python scripts/security_check.py --only tests --strict-known
```

Do not use real credentials in security test data or include sensitive values
in diagnostics or test output.
