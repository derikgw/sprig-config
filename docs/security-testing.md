# Security checks locally and in GitHub

These checks combine static analysis, dependency auditing, secret detection, and
generated security tests. Scanner alerts require review; a clean scan does not
prove that a repository is secure.

## Local setup

From `sprig-config-module`, using Python 3.11 or newer:

```sh
poetry config virtualenvs.in-project true --local
poetry install --without docs
uv tool install semgrep==1.182.1
poetry run python scripts/security_check.py
```

Poetry uses this project's `.venv`. Semgrep is installed separately to keep its
dependencies out of the library environment. The runner finds Semgrep on PATH
or in `~/.local/bin`. If you previously exported
`POETRY_VIRTUALENVS_IN_PROJECT=false`, unset it; environment overrides take
precedence over project-local Poetry configuration.

The runner executes every selected check even when an earlier one fails, and
returns a nonzero status if any check fails:

- Bandit scans the library source.
- Semgrep tests the checked-in rules, then scans the source with the community
  Python rules and the custom rules in `.semgrep/security.yml`. ERROR findings
  block the check; WARNING findings remain visible for triage. Scanner errors,
  missing/malformed reports, and scans with no source files also fail.
- pytest and Hypothesis exercise security properties using generated inputs.
- pip-audit checks the installed environment for known dependency advisories.
- A second pip-audit pass checks every exact pin in `poetry.lock`, including
  inactive platforms and documentation dependencies. It disables pip and
  dependency resolution so these packages are queried rather than installed.
  An installed-environment audit alone misses inactive conditional dependencies.

Semgrep's own summary may call findings "blocking"; the runner's documented
gate uses the report's ERROR severity. Custom diagnostic-value findings are
WARNINGs while the existing issue #41 work remains unresolved.

Reports are saved under `sprig-config-module/.security-reports/` (Git ignored).
Semgrep needs network access to fetch the current community Python rules;
the scanner version is pinned, but those upstream rules can change. Metrics
and version checks are disabled. pip-audit needs vulnerability database access.

## Focused and deeper runs

```sh
# Fast deterministic security tests: up to 50 examples per generated property.
poetry run python scripts/security_check.py --only tests

# Broader randomized exploration: up to 500 examples per property.
poetry run python scripts/security_check.py --only tests --deep

# Run every scanner and the broader tests.
poetry run python scripts/security_check.py --deep

# Treat the tracked hardening gaps as ordinary failures.
poetry run python scripts/security_check.py --only tests --strict-known

# Run a single scanner.
poetry run python scripts/security_check.py --only semgrep

# Audit every locked package, including inactive conditional dependencies.
poetry run python scripts/security_check.py --only lock-audit
```

`security_tests/` is separate from the existing test fixtures so these checks do
not load `.env` files or repository credential values. They use synthetic
markers, fresh test encryption keys, and temporary files. Generated checks cover
nested default redaction, explicit reveal round trips, import traversal,
outside-file symlinks, and literal encoded-path lookalikes.

Five issue #41 cases currently use **strict expected failures**: expanded YAML
error excerpts, decrypted binding errors, structural substitution, profile
traversal, and root symlinks. These are outstanding defects/policy gaps, not
passing security guarantees. Unexpected errors still fail, and fixing a case
causes an unexpected pass that requires removing its expected-failure annotation.
`--strict-known` disables all five annotations and should fail until hardening
is complete. See the [issue checklist](fix/security-hardening/41/README.md).

## GitHub Actions

The checked-in workflows run on pull requests, pushes to `main`, scheduled daily
runs, and manual dispatch. CodeQL uses the repository's existing managed setup:

| Workflow | Checks |
| --- | --- |
| `Security` | Existing Bandit, pip-audit, and Gitleaks jobs |
| `Security analysis` | Semgrep, security properties on Python 3.11/3.14, and all locked dependency pins |
| Managed CodeQL | Python and GitHub Actions analysis using the extended suite and local/remote sources |

Scheduled property tests use the deeper randomized profile. A manual Security
analysis run can enable `strict_known` to fail on unresolved issue #41 cases.
Semgrep JSON/SARIF and security test XML are retained as workflow artifacts for
14 days. SARIF uploads are skipped for fork PRs; the scanner gate still runs.
New workflow action references are pinned to commits, and Dependabot is
configured for weekly GitHub Actions and Python dependency updates.

Workflow files become active when pushed to GitHub; scheduled runs require them
on the default branch. CodeQL and SARIF results appear under the repository's
Security tab. CodeQL is configured through GitHub's managed default setup for
`actions` and `python`, with `query_suite=extended` and
`threat_model=remote_and_local`. Managed CodeQL has its own GitHub-controlled
schedule; the daily cron above applies to the checked-in workflows. There is no
duplicate CodeQL workflow to conflict with that managed setup.

After the new checks have run, repository administrators can require `Semgrep`,
`Security properties (Python 3.11)`, and `Security properties (Python 3.14)` in
the ruleset protecting `main`. Configure code scanning merge protection for
CodeQL alerts separately: successful analysis execution alone does not mean
there are no alerts. These repository settings are not changed by adding YAML.

GitHub secret scanning, push protection, and Dependabot security alerts are
separate repository settings. Gitleaks is already configured as a workflow;
its presence does not establish that GitHub's native settings are enabled.

## References

- [Semgrep Community Edition setup](https://docs.semgrep.dev/getting-started/quickstart-ce)
- [CodeQL workflow configuration](https://docs.github.com/en/code-security/reference/code-scanning/workflow-configuration-options)
- [Hypothesis](https://hypothesis.readthedocs.io/en/latest/)
