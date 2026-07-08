# claude-config

Live Claude Code config, synced across all machines. Tier: **large-exact** (see `~/sam-setup`).

- Whitelist `.gitignore`: only skills, agents, commands, hooks, CLAUDE.md, settings.json, keybindings, statusline sync. Sessions/caches/credentials never do.
- Sync: `hooks/session-start-pull.sh` pulls at session start; `hooks/session-end-push.sh` commits+pushes at session end. No manual git needed.
- New machine: `git clone git@github.com:samlayton99/claude-config.git ~/.claude` (bootstrap does this).
- Rule: no secrets, no binaries, no file >1MB.
