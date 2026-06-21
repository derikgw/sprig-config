# GitLab Merge Request Draft: GHSA-6v7p-g79w-8964

**Title**

`security: update msgpack to 1.2.1 for GHSA-6v7p-g79w-8964`

**Description**

## Summary

This MR refreshes the resolved `msgpack` dependency from `1.1.2` to `1.2.1`
for the development toolchain.

## Changes

- refresh the resolved `msgpack` package in `sprig-config-module/poetry.lock`
- refresh parent toolchain dependencies if required for Poetry to select
  `msgpack 1.2.1`

## Security Context

`GHSA-6v7p-g79w-8964` reports that repeated reuse of a `msgpack` `Unpacker`
after an error can crash the process with `SIGSEGV`, which can be used for
denial of service if untrusted input is processed repeatedly.

In this repository, `msgpack` is currently part of the default installed repo
environment via `pip-audit -> cachecontrol -> msgpack`. The published
`sprig-config` package still does not declare it in the `main` dependency set,
but GitLab CI uses plain `poetry install`, so the vulnerable version was
present at runtime for CI jobs and default local repo environments.

## Verification

- `poetry update msgpack`
- `poetry run pytest`
- `poetry run pip-audit`

## Backward Compatibility

- no changes to the published package's `main` dependency set
- no API changes
- no configuration changes required
