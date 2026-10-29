# Security hardening checklist

Tracking issue: [#41 — Harden configuration diagnostics, substitution, and file trust boundaries](https://github.com/derikgw/sprig-config/issues/41)

Branch: `fix/security-hardening`

This checklist records the repository review findings and remaining verification work. No critical or high-severity vulnerability was established. Checked items below record review conclusions; unchecked items are outstanding work.

## 1. Sensitive values in exceptions — Medium

**Status:** reproduced using extracted repository functions and synthetic markers. Actual credential exposure was not investigated.

Environment expansion precedes YAML parsing. Parser errors can include expanded source excerpts, which the loader propagates and the CLI prints to stderr. Separately, `ConfigValue(decrypt=True)` can decrypt a secret before a failed type conversion embeds the plaintext value in an exception. Exposure requires access to the resulting diagnostics; no remote disclosure endpoint was established.

Evidence:

- `sprig-config-module/src/sprigconfig/config_loader.py`: `_load_file()`, lines 253–266; `_expand_env()`, lines 268–273.
- `sprig-config-module/src/sprigconfig/parsers/yaml_parser.py`: `YamlParser.parse()`, lines 4–8.
- `sprig-config-module/src/sprigconfig/cli.py`: `run_dump()`, lines 59–61.
- `sprig-config-module/src/sprigconfig/injection.py`: `ConfigValue.__get__()`, lines 130–147; `ConfigValue._convert_type()`, lines 264–272.

Checklist:

- [ ] Remove sensitive values and expanded source excerpts from library-generated diagnostics.
- [ ] Ensure formatted exception chains cannot disclose the original values or parser excerpts.
- [ ] Review equivalent diagnostics in `instantiate()` and `ConfigurationProperties`.
- [ ] Add regression checks using synthetic markers, including decryption followed by conversion failure and CLI stderr.
- [ ] Preserve useful field names, expected types, and source positions in errors.

## 2. Environment substitution can inject structure — Conditional Medium

**Status:** structure injection reproduced with synthetic data. A lower-trust environment input in a deployed consumer was not established.

`_expand_env()` replaces text before parsing. A replacement intended for one scalar can introduce additional YAML keys or mappings. Security impact depends on whether a consumer allows a lower-trust party to supply such a replacement while trusting the surrounding configuration.

Evidence: `sprig-config-module/src/sprigconfig/config_loader.py`, `_load_file()` at lines 261–263 and `_expand_env()` at lines 268–273.

Checklist:

- [ ] Define substitution semantics and the trust required for replacement values.
- [ ] Prefer substitution within parsed scalar values so replacements cannot introduce document structure.
- [ ] Verify replacements cannot introduce keys, imports, or `_target_` entries.
- [ ] Test and document YAML, JSON, and TOML behavior, including quoting, newlines, defaults, missing variables, and resulting types.
- [ ] Assess compatibility with existing substitution usage before changing behavior.

## 3. Root/profile file containment — Conditional Low

**Status:** missing containment check confirmed by source inspection. A profile escape was demonstrated with a mocked filesystem; a real filesystem reproduction remains outstanding.

Root/profile selection does not apply the resolved-path containment check used for imports. A profile such as `dev/../../outside` can select an outside file if the required intermediate directory exists. Root-file symlinks also lack this containment enforcement. Security impact requires lower-trust profile input or relevant filesystem control; neither was established in a deployed consumer.

Evidence: `sprig-config-module/src/sprigconfig/config_loader.py`, `load()` at lines 151–154 and `_resolve_root_file()` at lines 194–204. Compare `_resolve_import()` at lines 226–240.

Checklist:

- [ ] Define the directory-confinement contract for root, profile, and imported files.
- [ ] Validate profile names against the supported profile syntax.
- [ ] Apply resolved-path containment to root/profile files if confinement is the intended contract.
- [ ] Decide and document the policy for root/profile symlinks.
- [x] Add real filesystem regression tests for profile traversal and symlinks using synthetic files (strict expected failures until hardening).
- [ ] Verify normal profiles, extension aliases, and in-directory imports continue working.

## 4. Dynamic instantiation trust boundary — Architectural concern

**Status:** dynamic import and invocation confirmed. A deployment vulnerability crossing an established trust boundary was not demonstrated.

Configuration passed to `instantiate()` selects an importable target and constructor parameters. Importing a module and invoking its target can execute code. Callers must trust this configuration as code. Loading configuration alone does not invoke `instantiate()`.

Evidence: `sprig-config-module/src/sprigconfig/instantiate.py`, `instantiate()` at lines 95–116 and 208–224; recursive instantiation at lines 155–172.

Checklist:

- [ ] Document code-level trust requirements for targets, parameters, nested targets, and imported modules.
- [ ] Decide whether restricted configuration sources are supported.
- [ ] If supported, evaluate a caller-supplied registry that enforces restrictions before importing targets and applies to nested targets.
- [ ] Avoid presenting module-name regex validation as an execution security boundary.

## 5. Example application hardening — Low-priority concern

**Status:** fallback signing-key pattern confirmed; an exploitable session/authorization path was not demonstrated.

The Flask example has a predictable fallback for `SECRET_KEY`. It also calls `load_config()` without the required `profile` argument and currently fails before reaching that assignment. These observations do not establish an exploitable deployed application.

Evidence: `sprig-config-module/examples/web-app/app.py`, `create_app()` at lines 21 and 33, and `main()` at line 121. Required argument: `sprig-config-module/src/sprigconfig/__init__.py`, `load_config()` at line 47.

Checklist:

- [ ] Correct the example's configuration-loading calls.
- [ ] Require an explicitly configured signing key when the example uses security-sensitive signing behavior.
- [ ] Document development-only behavior and verify the example's startup flow.

## Review conclusions that do not establish vulnerabilities

- [x] No bypass of the import `resolve()` followed by `relative_to(base)` check was demonstrated by the proposed encoded-path or ordinary symlink examples. Missing tests alone do not establish a vulnerability.
- [x] Explicit `reveal_secrets=True` and CLI `--secrets` are intentional operations; default redaction was not shown to be bypassed through these flags.
- [x] Deferred rejection of invalid Fernet ciphertext does not independently establish a confidentiality or integrity failure.
- [x] Excluding tests from Bandit is a scanning-scope choice, not a vulnerability by itself.
- [x] Best-effort Python memory cleanup is a documented limitation, not a newly demonstrated vulnerability.
- [ ] Clarify that default serialization redacts `LazySecret` wrappers, rather than detecting every sensitive plaintext configuration value.

## 6. Conditional dependency advisory — Critical advisory severity

**Status:** GitHub Dependabot alert [#99](https://github.com/derikgw/sprig-config/security/dependabot/99)
identified `brotlicffi==1.2.0.1` in `sprig-config-module/poetry.lock` as affected
by `GHSA-9v8h-qqgm-4m35` / `PYSEC-2026-4323`. This is a confirmed vulnerable
dependency pin, not a demonstrated critical exploit in SprigConfig. The
dependency is conditional and absent from the audited CPython environment.

- [x] Reproduce the advisory by auditing every lockfile pin, independent of the installed environment.
- [x] Update the lock entry to patched `brotlicffi==1.2.1.0` without changing other locked versions.
- [x] Add local/CI lockfile auditing that includes inactive platforms and dependency groups without installing them.
- [x] Verify the updated complete lockfile audit reports no known vulnerabilities.
- [ ] Merge the patch and verify GitHub closes the default-branch alert.

## Verification and completion

The review used source inspection and isolated extracted-function checks with synthetic values and mocked filesystem/environment access. The complete package test suite could not run with the available compatible dependencies. No dependencies were installed, credential stores inspected, or repository secrets decrypted during verification. Git history secret scanning and a current dependency vulnerability audit were outside the completed review.

- [x] Reproduce relevant cases through the complete package on a supported Python environment (Python 3.14; see `security_tests/test_known_findings.py`).
- [ ] Run focused regression tests and required repository checks after implementation.
- [ ] Record final behavior, validation results, compatibility decisions, and any remaining limitations here or in the linked issue.

## Security check infrastructure

Local and GitHub scanning setup is documented in [Security checks](../../../security-testing.md).
Semgrep and generated security tests supplement the existing Bandit, pip-audit,
and Gitleaks workflow. Five known issue cases remain explicit strict expected
failures, and five Semgrep diagnostic-value findings remain visible as warnings.
Infrastructure setup does not mark the hardening fixes above complete.

Validation after adding the lockfile audit: 16 tests passed and five documented
issue cases remained expected failures under the deep generated-test profile.
Strict-known mode previously reproduced all five failures. Semgrep's four custom
rule tests passed; scanning found five diagnostic-value warnings and no ERROR
findings. Bandit and the installed-environment audit passed, and the expanded
lockfile audit passed after the conditional dependency patch. Ruff, actionlint,
and Poetry lock validation passed. The initial draft PR's GitHub checks passed;
the lockfile audit is included in the follow-up revision.
