#!/bin/bash
# SessionEnd hook: commit and push any config changes (skill edits, settings).
# Whitelist .gitignore means only portable config is ever staged.
#
# Conflict handling (loss-proof by construction):
#   fetch fails        -> offline; retry next session
#   fast-forward       -> plain push
#   rebase conflicts   -> preserve local commits on a pushed stranded/ branch,
#                         then spawn a headless resolver (sync-resolver.sh).
#                         Nothing is ever discarded: the stranded branch is the
#                         permanent undo point for whatever resolution follows.
cd "${CLAUDE_SYNC_DIR:-$HOME/.claude}" || exit 0
[ -n "$CLAUDE_SYNC_RESOLVER" ] && exit 0  # resolver's own SessionEnd: no recursion
export GIT_TERMINAL_PROMPT=0
DEVICE="$(cat "$HOME/.sam-device" 2>/dev/null || hostname -s)"

# Never start from a stuck rebase (a prior conflicted pull would otherwise
# wedge the repo silently forever).
if [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ]; then
  git rebase --abort 2>/dev/null
fi

git add -A 2>/dev/null
if ! git diff --cached --quiet 2>/dev/null; then
  git commit --quiet -m "sync: ${DEVICE} $(date '+%Y-%m-%d %H:%M')" 2>/dev/null
fi

# Push whenever local is ahead — this session's commit AND any commit stranded
# by an earlier failed push (otherwise a no-change session never retries and
# the machines silently diverge).
if [ -n "$(git log --oneline '@{u}..HEAD' 2>/dev/null)" ]; then
  git fetch --quiet 2>/dev/null || exit 0  # offline, not a conflict: retry later

  if git merge-base --is-ancestor origin/main HEAD 2>/dev/null; then
    git push --quiet 2>/dev/null  # origin didn't move: clean fast-forward push
  elif git rebase --quiet origin/main >/dev/null 2>&1; then
    git push --quiet 2>/dev/null  # local-only commits replayed cleanly
  else
    # Real conflict. Preserve local commits on a pushed branch FIRST, then
    # hand off to the resolver. Marker file surfaces it in future sessions
    # (untracked by the whitelist .gitignore, so machine-local).
    git rebase --abort 2>/dev/null
    BRANCH="stranded/${DEVICE}-$(date '+%Y%m%d-%H%M%S')"
    git branch "$BRANCH" 2>/dev/null
    git push --quiet origin "$BRANCH" 2>/dev/null
    printf '%s\n' "$BRANCH" > .sync-conflict
    HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
    nohup "$HOOK_DIR/sync-resolver.sh" "$BRANCH" >/dev/null 2>&1 &
  fi
fi

# Hygiene: prune stranded branches that are merged into origin/main (zero data
# loss — their content is in main's history) and older than 60 days.
CUTOFF=$(( $(date +%s) - 60*24*3600 ))
git for-each-ref --format='%(refname:short) %(committerdate:unix)' refs/heads/stranded 2>/dev/null |
while read -r ref when; do
  if [ "$when" -lt "$CUTOFF" ] && git merge-base --is-ancestor "$ref" origin/main 2>/dev/null; then
    git branch -D "$ref" >/dev/null 2>&1
    git push --quiet origin --delete "$ref" 2>/dev/null
  fi
done
exit 0
