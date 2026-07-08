Manage Claude Code sessions for the current project.

Run: `~/.claude/scripts/sessions.sh $ARGUMENTS`

After running the script, you MUST repeat the output as a text message so the user can see it. Do not rely on the tool output being visible.

Format the session list as a clean markdown table with columns: Session, Date, Size, Messages. Mark the active session with `(active)`. Show the flags section below the table.

When output contains `AWAITING_CONFIRMATION`, ask the user to confirm before re-running with `--yes`.
