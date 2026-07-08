---
name: update-repos
description: >
  Keep a workspace of local git repos in sync with a GitHub org. Clones any
  non-archived repos missing locally, then fast-forward-pulls every repo
  whose working tree is clean and on the default branch. Safe by default —
  never stashes, resets, or creates merge commits. Any repo that can't be
  cleanly updated (dirty, feature branch, diverged, detached) is left
  untouched and surfaced for interactive follow-up. Use when the user says
  "update my repos", "pull latest on all repos", "sync repos", "/update-repos",
  or when starting work in a workspace that may be behind the org.
---

# update-repos

Bulk-syncs a workspace of local git repos with their GitHub org.

## Invocation

Call the script directly — the safe, non-destructive bulk pass runs without permission prompts because the script path is allowlisted.

```
bash ~/.claude/skills/update-repos/scripts/update-repos.sh [PATH] [--org ORG]
```

- `PATH` — defaults to `$PWD`. If it contains a child dir named `repos/`, that dir is scanned; otherwise `PATH` itself is the repos folder.
- `--org` — optional. If omitted, the majority GitHub org among existing repos' `origin` URLs is used. No existing GitHub repos → clone phase is skipped.

## What the script does

1. Enumerates non-archived repos in the org via `gh repo list` and clones any missing into the repos folder.
2. For each local repo: `git fetch --prune origin`, then `git merge --ff-only origin/<default>` if the repo is on its default branch with a clean working tree.
3. Leaves every other repo untouched (dirty, on a feature branch, diverged, detached, no origin).
4. Prints:
   - Cloned list (if any)
   - Pulled table, sorted by commit count desc (up-to-date rows excluded)
   - One-line totals: `N cloned, N pulled, N up-to-date, N need attention.`

## After the summary

The script itself does not attempt to resolve conflicts, rebase, stash, or mutate any non-clean repo. It surfaces the "need attention" count. As the calling agent, walk those repos one at a time:

1. For each repo not in `PULLED` or `UP_TO_DATE`, identify what's wrong (dirty files, current branch vs. default, diverged commits).
2. Propose a specific next step and wait for user approval.
3. Resolution commands (`git merge`, `git checkout`, file edits, `git add`, `git commit`, etc.) are NOT in the allowlist and will trigger normal permission prompts.

## Output contract (for agents)

`update-repos.sh` exits 0 on completion regardless of per-repo outcomes. Parse stdout:
- Lines under `Pulled:` list successful fast-forwards with commit counts.
- The final totals line gives counts. If `N need attention` > 0, re-enumerate local repos and run `git status` / `git branch --show-current` to build the attention queue.

## Non-goals

No scheduling, no parallelism, no pushing, no branch creation, no automatic conflict resolution, no deletion of local repos that disappeared from the org.

## Related

- `/update-index` — maintains `<workspace>/INDEX.md`, a machine-generated scaffolding file that tells future agents which repos are relevant for high-level questions (e.g., "describe the customer experience", "how is ACU computed?"). Run `/update-index` after a pull to refresh the index; `/update-repos --with-index` prints a hint at the end reminding the calling agent to do this. The two skills are deliberately separate — `/update-repos` is fast and deterministic; `/update-index` is agent-orchestrated and more expensive, so you don't pay that cost every time you pull.
