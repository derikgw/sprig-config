---
title: Site Operations
---

# Site Operations

This page documents the repository settings required for SprigConfig documentation publishing.

## Canonical docs URL

- Site URL: `https://derikgw.github.io/sprig-config/`

## Required repository settings

The repository must keep these settings aligned:

1. **Repository homepage URL**
   - Must be set to the docs site URL so the Website link appears on the repository page.
2. **GitHub Pages build source**
   - Should use **GitHub Actions** (workflow-based deployment), not legacy branch-folder mode.

## Workflow used for deployment

- [pages.yml](../.github/workflows/pages.yml)

Key behavior:
- deploys docs on pushes to `main` that touch `docs/**`
- supports manual dispatch
- validates local docs links before deploy
- deploys via artifact-based Pages actions

## Verification checklist

After updates to docs publishing:

1. Confirm repository Website link exists on the repo page.
2. Confirm Pages shows workflow-based publishing.
3. Confirm latest Pages workflow run completed successfully.
4. Confirm docs URL serves the expected updates.
