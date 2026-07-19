# Maintainer Documentation

This directory contains documentation for people developing and releasing
SprigConfig. User-facing documentation is maintained in the repository-level
`docs/` directory. GitHub Pages currently publishes that directory with Jekyll;
MkDocs provides local preview and strict documentation validation.

## Active maintainer guides

- `README_Developer_Guide.md` — local setup, architecture, and contribution flow
- `dependency-management.md` — dependency and security update workflow
- `release_checklist.md` — release verification checklist
- `PyPI.md` — package publishing configuration and procedures
- `GitLab.md` — remaining GitLab pipeline behavior during the GitHub migration
- `building_documentation.md` — documentation tooling and publishing
- `git_skip_worktree_for_test_config_files.md` — specialized test-fixture workflow

These operational guides should be checked against CI configuration whenever
the workflows change.

## Detailed implementation references

- `configuration-injection.md`
- `dependency-injection-explained.md`
- `SprigConfig_ENC_BestPractices.md`
- `migration_guide.md`

Concise usage instructions belong in the public `docs/` tree. These longer
documents are implementation or migration references and should not duplicate
the public API contract.

## Historical artifacts

Files named `gitlab-issue-*` and `gitlab-mr-*` are snapshots of past issue and
merge-request descriptions. They are not current product documentation and
should be moved to issue trackers or an archive in a future cleanup.

`AI_Info.md` and `code-metrics.md` record development process and point-in-time
analysis. Treat them as project records, not usage guidance.

## Documentation rules

1. The code and executable tests define behavior.
2. Public APIs and examples belong under the root `docs/` directory.
3. Maintainer procedures belong here and should link to workflow files rather
   than restating them line by line.
4. Design proposals under `docs/AOP/`, per-module Markdown under `src/`, and
   per-test Markdown under `tests/` are not public API documentation.
5. Run `poetry run mkdocs build --strict` and the full test suite before merging
   documentation changes.
