# SprigConfig Test Suite Guide

This is the index to the test suites under `tests/` and their companion
documentation. The source tests are the executable specification; suite docs
explain their intent and the scope of their evidence.

## Reading test evidence

A passing test establishes that the asserted behavior held for the code,
fixtures, and inputs exercised by that test. It does not by itself establish
universal correctness, production safety, performance, or absence of other
failure modes. Security tests are especially bounded: synthetic inputs verify
specific paths and output surfaces, not every possible exception, logger, or
consumer.

Prefer wording such as “the test verifies/asserts” over “proves,” “guarantees,”
or “is secure.” For each test suite, the companion document should make clear:

1. **Intent** — the behavior or regression being exercised.
2. **Setup and observation** — which inputs are prepared and which output or
   state is asserted.
3. **Evidence** — what a passing assertion supports.
4. **Limits** — what the test does not exercise or establish.
5. **Command** — how to run the test.

Tests generally use temporary directories or the shared fixtures described in
[conftest.md](./conftest.md). Avoid changing committed files under `tests/config`
from a test; use `tmp_path` or the `full_config_dir` copy fixture when mutation
is needed.

## Suite index

Run commands below from `sprig-config-module/`, typically with
`poetry run pytest <path>`.

| Test module and documentation | Intent and what the assertions observe | Evidence limits |
|---|---|---|
| [test_cli.py](./test_cli.md) | Runs the module CLI as a subprocess; checks output, exit status, and output-file behavior. | Covers these CLI invocations, not every command, terminal, or logging configuration. |
| [test_config.py](./test_config.md) | Checks mapping-style access, nested wrapping, dotted lookup, conversion to dict, and YAML output. | The tested copy behavior does not imply the entire `Config` object is immutable. |
| [test_config_singleton.py](./test_config_singleton.md) | Checks initialization, identity, concurrent initialization, test reload/clear behavior, and access through the singleton. | Thread tests exercise their constructed race, not every scheduling or application lifecycle. |
| [test_deep_merge.py](./test_deep_merge.md) | Checks representative merge, overlay, import, list replacement, cycle, and dotted-access cases using repository fixtures. | Fixture examples do not exhaust all tree shapes or prove a global merge ordering for every input. |
| [test_full_merge_provenance.py](./test_full_merge_provenance.md) | Loads the `dev` fixture tree and compares expected source paths, selected metadata fields, and selected merged values. | It is one fixed YAML fixture and selected assertions, not a general audit of all files, formats, or configuration semantics. |
| [test_import_trace.py](./test_import_trace.md) | Checks trace entry fields, selected direct-import relationships, monotonic order, and alignment with `sources`. | The fixture currently has direct imports; the test named `nested_imports` does not exercise a genuinely nested import chain. |
| [test_injection.py](./test_injection.md) | Exercises `ConfigValue`, `ConfigurationProperties`, and `config_inject`, including selected conversion errors. | Does not cover every custom type conversion or every user-defined exception path. |
| [test_instantiate.py](./test_instantiate.md) | Checks target loading, constructor parameters, recursion, type conversion, and error cases. | Uses local test classes/configs; not a sandbox or security boundary for untrusted `_target_` configuration. |
| [test_integration.py](./test_integration.md) | Combines loader, profile, import, metadata, environment, secret, CLI-adjacent API, and singleton behavior in representative flows. | Integration coverage is limited to the listed fixture flows and synthetic test inputs. |
| [test_meta.py](./test_meta.md) | Checks active-profile metadata and selected interactions with user configuration. | Does not validate every `_meta` field; metadata source/trace details have separate suites. |
| [test_meta_sources.py](./test_meta_sources.md) | Reads top-level YAML imports from the test fixture and checks the expected loaded source paths. | The helper and assertions are YAML-fixture-specific; they do not establish format parity or independently verify every ordering rule. |
| [test_positional_import_nested_merges_in_place.py](./test_positional_import_nested_merges_in_place.md) | Checks one fixture result at `etl.jobs.etl.jobs.foo`. | It does not assert trace contents, sibling preservation, CLI output, or broad positional-import behavior. |
| [test_profiles.py](./test_profile_behavior.md) | Checks profile overlays, missing profiles, profile imports, selected precedence, metadata, and dotted access. | Assertions apply to the repository's named fixture profiles; they are not exhaustive over profile names or filesystem paths. |
| [test_subdirectory_imports.py](./test_subdirectory_imports.md) | Checks that an ordinary in-directory subdirectory import loads its selected value. | Does not exercise path escape rejection; security boundary cases are under `security_tests/`. |
| [test_target_config.py](./test_target_config.md) | Directly constructs a local adapter and checks its fields. | This smoke test does not exercise `instantiate()` or configuration loading. |
| [test_toml_support.py](./test_toml_support.md) | Checks TOML loading, imports, overlays, and substitution. | Covers its test documents, not all TOML grammar or substitution contexts; parser diagnostic redaction is covered in `security_tests/`. |
| [test_validation.py](./test_validation.md) | Checks opt-in dataclass schema validation, selected errors, legacy behavior without a schema, merged input, and three-format parity. | It covers the defined schema/value cases, not every Python typing construct or all malformed schemas. |

### Security tests

The dedicated [security test guide](../security_tests/README.md) indexes the
security suite and describes the evidence limits. Security-focused tests live
under `security_tests/`; functional suites under `tests/` focus on API and
feature behavior.

## Running tests

From `sprig-config-module/`:

```bash
poetry run pytest
poetry run pytest tests/test_injection.py
poetry run pytest security_tests
```

Relevant optional controls and shared fixtures are documented in
[conftest.md](./conftest.md). Do not use secret-revealing dump options with real
credentials or in logs intended for sharing.
