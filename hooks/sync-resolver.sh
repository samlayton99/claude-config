#!/bin/bash
# Spawned in the background by session-end-push.sh when a sync rebase hit real
# conflicts. Runs a headless Claude session to merge origin/main into main.
#
# Safety model:
#   - The pre-resolution local state is already on a pushed stranded/ branch;
#     the resolver merges (never rebases/force-pushes), so both lineages stay
#     in history permanently. Any resolution mistake is recoverable via
#     `git show <stranded-branch>:<file>`.
#   - The agent must not guess on large deletions: it aborts and a macOS
#     notification + the .sync-conflict marker escalate to an interactive
#     session instead.
#   - This script (not the agent) verifies success and clears the marker.
REPO="${CLAUDE_SYNC_DIR:-$HOME/.claude}"
cd "$REPO" || exit 0
BRANCH="$1"
[ -n "$BRANCH" ] || exit 0
export GIT_TERMINAL_PROMPT=0
export CLAUDE_SYNC_RESOLVER=1  # keeps the spawned session's hooks from recursing

LOG_DIR="$REPO/sync-conflicts"   # untracked (whitelist .gitignore): machine-local
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/log.txt"
note() { printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M')" "$*" >> "$LOG"; }

notify() {
  osascript -e "display notification \"$1\" with title \"claude-config sync\"" 2>/dev/null
}

# One resolver at a time; a lock older than 60 min is from a crash — take over.
LOCK="$REPO/.sync-resolver-lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  AGE=$(( $(date +%s) - $(stat -f %m "$LOCK" 2>/dev/null || echo 0) ))
  [ "$AGE" -lt 3600 ] && exit 0
  rmdir "$LOCK" 2>/dev/null; mkdir "$LOCK" 2>/dev/null || exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

# Already resolved (e.g. a second stranding raced an earlier resolver)?
git fetch --quiet 2>/dev/null
if [ -z "$(git log --oneline 'origin/main..HEAD' 2>/dev/null)" ]; then
  rm -f .sync-conflict; note "no-op: already in sync"; exit 0
fi

CLAUDE_BIN="$(command -v claude || ls "$HOME/.local/bin/claude" 2>/dev/null | head -1)"
if [ -z "$CLAUDE_BIN" ]; then
  note "FAILED: claude binary not found; conflict left for interactive session ($BRANCH)"
  notify "Sync conflict needs attention (no claude binary)"
  exit 0
fi

note "resolver started for $BRANCH"
"$CLAUDE_BIN" -p "You are an automated sync-conflict resolver for the git repo at $REPO (Sam's Claude config, synced across machines).

State: local 'main' has diverged from origin/main. The local side is fully preserved on branch '$BRANCH', already pushed to origin — so nothing can be permanently lost, no matter what you do here.

Task: merge origin/main into main, resolve conflicts, push main.

Rules:
1. git fetch, then git merge origin/main. A merge, NOT a rebase — both lineages must remain in history. Never force-push, never amend or rewrite existing commits.
2. When resolving conflicted files, NEVER discard content. Keep both sides' changes wherever coherent. For JSON/YAML the result must stay valid while containing both sides' keys; where the exact same key has two different scalar values, keep the newer side's value.
3. If a correct resolution would require deleting a whole file or a block larger than ~30 lines and the right choice is not obvious from the content itself, DO NOT GUESS: run 'git merge --abort' and stop. A human will decide in the next interactive session.
4. Commit message for the merge: 'sync-resolve: merge origin/main (local side preserved on $BRANCH)'. Then git push.
5. Work only inside $REPO. Touch nothing else.

End by briefly listing which files conflicted and how each was resolved." \
  --allowedTools "Bash(git:*),Read,Edit,Write,Grep,Glob" \
  --max-turns 40 >> "$LOG" 2>&1
echo "" >> "$LOG"

# Verify with git, not with the agent's own claims.
if [ -z "$(git log --oneline 'origin/main..HEAD' 2>/dev/null)" ] \
   && [ ! -f .git/MERGE_HEAD ] && git diff --quiet 2>/dev/null; then
  rm -f .sync-conflict
  note "resolved and pushed ($BRANCH kept as undo point)"
  notify "Sync conflict auto-resolved; undo point: $BRANCH"
else
  git merge --abort 2>/dev/null
  note "NOT auto-resolved: needs a decision ($BRANCH); see this log"
  notify "Sync conflict needs your decision — open any claude session"
fi
exit 0
