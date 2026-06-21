# GitLab Issue Draft: GHSA-6v7p-g79w-8964

**Title**

`security: update msgpack to 1.2.1 for GHSA-6v7p-g79w-8964`

**Description**

## Summary

Upgrade the resolved `msgpack` dependency in `sprig-config-module` from `1.1.2`
to `1.2.1` to remediate `GHSA-6v7p-g79w-8964`.

## Vulnerability Metadata

- Advisory: `GHSA-6v7p-g79w-8964`
- Dependency: `msgpack`
- Current resolved version: `1.1.2`
- Fixed version: `1.2.1`
- Dependency path: `pip-audit -> cachecontrol -> msgpack`

## Background

The advisory states that if `msgpack`'s `Unpacker` is reused after an error, a
process can crash with `SIGSEGV`. In workflows that repeatedly unpack
untrusted input, that can become a denial-of-service risk.

In this repository, `msgpack` is not a direct main dependency of the published
`sprig-config` package. It is currently resolved into the default repository
environment through `pip-audit -> cachecontrol -> msgpack`.

That distinction matters here because this repository's GitLab CI setup uses
plain `poetry install`, which installs the dev toolchain into the job
environment. As a result, the vulnerable `msgpack` release is present at
runtime for CI jobs and for local repo environments created with the default
Poetry install flow, even though it is not part of the package's `main`
dependency group.

## Scope

- Refresh `sprig-config-module/poetry.lock` so the resolved dependency graph
  installs `msgpack 1.2.1`
- If needed, refresh parent toolchain packages so Poetry can select the fixed
  `msgpack` release
- Run local verification where feasible

## Acceptance Criteria

- `sprig-config-module/poetry.lock` resolves `msgpack` to `1.2.1`
- Security scanning no longer reports `GHSA-6v7p-g79w-8964`
- Regression checks complete successfully

## Risk / Compatibility

- Expected risk is low because this is a patch-level transitive dependency
  refresh
- No runtime dependency behavior changes are expected for SprigConfig
  consumers
- No API or configuration changes are expected

## Verification

- `poetry update msgpack`
- `poetry run pytest`
- `poetry run pip-audit`

## Notes

- This vulnerability affects the default repository runtime environment used by
  CI and local development installs, even though it is not in the published
  package's `main` dependency set
- If Poetry cannot select `1.2.1` directly, refresh the parent dependency path
  beginning with `cachecontrol` or `pip-audit`
