## Core Principles

- Never use emojis.

## Commit Authorship

When committing code changes:
- Never add Claude as a commit author.
- Always commit using the default git settings.

## Documentation Style

When creating or updating markdown documentation files:
- **Never create .md files unless explicitly instructed.**
- **Be extremely concise** - engineers scan, they don't read novels
- **Only include essential information** - what they need to know, not what's possible to explain
- **Prefer examples over prose** - show the pattern, not the theory
- **Assume technical competence** - skip obvious explanations
- **Front-load critical info** - put warnings and key concepts first
- **Delete verbose explanations** - if it takes more than 3 sentences, it's probably too long

Default to 1-2 sentence explanations. Only expand when complexity absolutely requires it.

## Python venvs under iCloud (TDD)

- `~/Desktop` and `~/Documents` are iCloud-synced; a project-local `.venv` gets its `lib/` evicted (pip + site-packages silently vanish). Put venvs OUTSIDE iCloud at `~/venv/<project>` — plain `python3 -m venv` + pip. (`~/.venvs` is a compatibility symlink to `~/venv`. Reusable shared envs live there too, e.g. `general_ml`, `webdev`.)
- You CAN run the suite yourself: `~/venv/<project>/bin/python -m pytest -q`. Don't assume the sandbox blocks the venv — verify with a quick import probe, then run it.
