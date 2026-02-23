#!/usr/bin/env bash
# Pre-commit hook: remind developers about skip-worktree files.
# These files have local changes hidden from git, so intentional
# modifications require explicitly clearing the flag before staging.

files=$(git ls-files -v | grep "^S" | cut -c3-)

if [ -n "$files" ]; then
    echo ""
    echo "These files have skip-worktree set (changes are hidden from git):"
    echo "$files" | while read -r f; do echo "   $f"; done
    echo ""
    echo "If you intended to modify any of these, run:"
    echo "   git update-index --no-skip-worktree <file>"
    echo "   git add <file>"
    echo ""
fi
