#!/bin/bash
# SessionStart hook: pull latest claude config. Fast, quiet, offline-tolerant.
# Fast-forward only — never merges, never blocks a session on a conflict.
cd "$HOME/.claude" || exit 0
export GIT_TERMINAL_PROMPT=0
git pull --ff-only --quiet 2>/dev/null || true
exit 0
