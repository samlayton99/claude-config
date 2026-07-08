#!/bin/bash
# SessionEnd hook: commit and push any config changes (skill edits, settings).
# Whitelist .gitignore means only portable config is ever staged.
cd "$HOME/.claude" || exit 0
export GIT_TERMINAL_PROMPT=0
DEVICE="$(cat "$HOME/.sam-device" 2>/dev/null || hostname -s)"
git add -A 2>/dev/null
if ! git diff --cached --quiet 2>/dev/null; then
  git commit --quiet -m "sync: ${DEVICE} $(date '+%Y-%m-%d %H:%M')" 2>/dev/null
  # Rebase-pull first so two machines pushing the same day don't reject.
  git pull --rebase --quiet 2>/dev/null || true
  git push --quiet 2>/dev/null || true
fi
exit 0
