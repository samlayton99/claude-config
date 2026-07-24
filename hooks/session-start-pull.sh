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

# Same pattern for sam-setup: its daily capture auto-resolves capture-owned
# conflicts, but hand-edited files strand with a marker — surface that here.
if [ -f "$HOME/sam-setup/.sync-stuck" ]; then
  echo "SAM-SETUP SYNC STUCK: the daily capture could not reconcile ~/sam-setup with origin ($(head -1 "$HOME/sam-setup/.sync-stuck" 2>/dev/null) attempts) — a hand-edited file conflicts. Local commits are preserved on origin branch 'stranded-<device>'. Offer to fix: inspect with 'git -C ~/sam-setup log --oneline origin/main..HEAD', merge origin/main keeping both sides (never force-push main, never discard content), push; capture clears .sync-stuck on the next run."
fi
exit 0
