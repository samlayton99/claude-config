# claude-config

Thin, machine-independent Claude Code config. Tier: **large-exact** (see `~/sam-setup/settings/large-exact/claude.md`).

- Tracked: `CLAUDE.md` (two `@import` lines into the shared context repo), `keybindings.json`, `statusline-command.sh`. Identical on every machine by design.
- Not tracked, on purpose: `settings.json` (machine-specific; sam-setup captures it per device), `skills/`, `agents/`, `commands/` (symlinks that `codex-config/bin/install-context` regenerates), sessions, caches, credentials, auto-memory (machine-local by Sam's decision, 2026-09-15).
- Sync: the daily sam-setup capture fast-forwards this clone and commits+pushes tracked changes; it refuses divergence and reports it. No session hooks.
- New machine: `git clone git@github.com:samlayton99/claude-config.git ~/.claude`, then `python3 ~/my-repos/projects/tools/codex-config/bin/install-context`.
- History before 2026-09-15 (the old whole-config layout) is on branches `final-mac-mini-2026` and `final-personal-macbook`.
