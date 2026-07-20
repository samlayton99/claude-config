#!/bin/bash
# SessionStart hook: pull latest claude config. Fast, quiet, offline-tolerant.
# Fast-forward only — never merges, never blocks a session on a conflict.
cd "${CLAUDE_SYNC_DIR:-$HOME/.claude}" || exit 0
export GIT_TERMINAL_PROMPT=0
git pull --ff-only --quiet 2>/dev/null || true

# Surface an unresolved sync conflict into this session's context so the agent
# can offer to fix it. The stranded/ branch named in the marker is the pushed,
# permanent copy of the local side — resolution must merge, never discard.
if [ -f .sync-conflict ] && [ -z "$CLAUDE_SYNC_RESOLVER" ]; then
  echo "UNRESOLVED ~/.claude SYNC CONFLICT: local main diverged from origin/main and auto-resolution did not complete. Local commits are preserved on pushed branch '$(cat .sync-conflict)'. Details: sync-conflicts/log.txt. Offer to resolve by merging origin/main into main (keep both sides, never force-push, never discard content); on success remove .sync-conflict."
fi
exit 0
