# Handling Test Config Files with Git (skip-worktree)

This repository contains **test configuration files that are intentionally modified during test runs**.

To prevent these changes from being accidentally staged or committed, we use Git’s **`skip-worktree`** mechanism.

This document explains *why* this is needed and *how* to work with it safely.

---

## Why This Exists

Some files under:

```
tests/config/
```

are mutated as part of automated tests (for example, secrets injection, write-back behavior, or runtime normalization).

These changes are:
- Expected
- Local-only
- Not meaningful to commit

However, the files **must remain tracked** by Git so tests have a known starting state.

`skip-worktree` solves this exact problem.

---

## What `skip-worktree` Does

When a file is marked with `skip-worktree`:

- ✅ The file remains **tracked** by Git
- ✅ Local modifications are **ignored by `git status`**
- ✅ `git add .` will **not stage the file**
- ✅ You can still explicitly stage the file when you *intend* to commit changes

This is **not the same** as `.gitignore` and is safe for this use case.

---

## Marking a File as skip-worktree

From the repository root:

```bash
git update-index --skip-worktree tests/config/application-secrets.yml
```

You may apply this to multiple files:

```bash
git update-index --skip-worktree tests/config/*.yml
```

After this, `git status` should no longer show changes for those files.

---

## Intentionally Committing a Change

If you *do* want to commit an update to one of these files:

```bash
git update-index --no-skip-worktree tests/config/application-secrets.yml
git add tests/config/application-secrets.yml
```

After committing, it is recommended to re-apply `skip-worktree`:

```bash
git update-index --skip-worktree tests/config/application-secrets.yml
```

This makes intent explicit and avoids accidental commits later.

---

## Do NOT Use `assume-unchanged`

You may see advice online suggesting:

```bash
git update-index --assume-unchanged <file>
```

**Do not use this here.**

Reasons:
- It is intended as a *performance hint*, not a workflow tool
- Git may silently re-detect changes
- Behavior is unreliable across merges and rebases

For intentional local divergence, **`skip-worktree` is the correct choice**.

---

## Notes

- `skip-worktree` is **local-only** and does not affect other developers
- Each developer must apply it on their own machine
- CI environments should **not** use `skip-worktree`

---

## Summary

Use `skip-worktree` when:
- Files must be tracked
- Tests legitimately modify them
- Changes should not be committed accidentally

This repository intentionally uses that pattern for certain test config files.

