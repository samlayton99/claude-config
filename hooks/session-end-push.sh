#!/bin/bash
# SessionEnd hook: commit and push any config changes (skill edits, settings).
# Whitelist .gitignore means only portable config is ever staged.
cd "$HOME/.claude" || exit 0
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
# the machines silently diverge). Rebase-pull first so two machines pushing
# the same day don't reject; abort a conflicted rebase rather than wedge.
if [ -n "$(git log --oneline '@{u}..HEAD' 2>/dev/null)" ]; then
  if ! git pull --rebase --quiet 2>/dev/null; then
    git rebase --abort 2>/dev/null
    exit 0
  fi
  git push --quiet 2>/dev/null
fi
exit 0
