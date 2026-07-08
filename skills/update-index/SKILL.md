---
name: update-index
description: >
  Build or update INDEX.md — a machine-generated scaffolding file that
  points future agents at which repos in a workspace are relevant for a
  high-level question. Runs either a full init (first time; expensive,
  dispatches one subagent per repo in parallel) or a conservative update
  (cheap; most calls change nothing). Use when the user says "build the
  index", "update the index", "refresh the workspace index",
  "/update-index", or after /update-repos has pulled substantial changes.
---

# update-index

Builds and maintains `<workspace>/repos/INDEX.md` (or `<workspace>/INDEX.md`
when the workspace has no `repos/` subfolder) — a directive scaffolding that
future agents read to answer high-level questions ("how is ACU computed?",
"describe the current customer experience", "what are fixed vs. variable
costs?"). INDEX.md is co-located with the repos it indexes; the
`.update-index/` state dir stays at the workspace root.

**This skill is agent-orchestrated, not script-only.** The bash scripts do
discovery and assembly; the real work is dispatching subagents that each
explore one repo.

## Invocation

You may be invoked with:
- No args → use `$PWD` as the workspace root.
- A path arg → use that as the workspace root.
- `--force` → run init even if INDEX.md exists.

The workspace root is the directory containing a `repos/` subfolder (or the
repos folder itself). `INDEX.md` lives inside `repos/` when the workspace
has one (so it sits next to the repos it indexes); otherwise it lives at the
workspace root. `.update-index/` always lives at the workspace root.

## Workflow

### Step 1 — Discovery

Run:
```
bash ~/.claude/skills/update-index/scripts/discover.sh <workspace>
```

Parse the TSV output. Each line is:
```
<name>\t<abs_path>\t<current_head_sha>\t<has_remote>\t<state>
```
Where `<state>` is `CLEAN_ON_DEFAULT`, `BEHIND_DEFAULT_DIRTY`,
`FEATURE_BRANCH`, `DETACHED`, `NO_REMOTE`, or `EMPTY_REMOTE`.

### Step 2 — Choose mode

- If INDEX.md does not exist (use `index_exists <workspace>` from lib.sh — it checks the correct location), OR `--force` is set → **init mode**.
- Otherwise → **update mode**.

### Step 3a — Init mode

1. Source the lib and init the state dir:
   ```
   source ~/.claude/skills/update-index/scripts/lib.sh
   init_state_dir <workspace>
   ```
2. Read the prompt template:
   ```
   PROMPT_TEMPLATE="$(cat ~/.claude/skills/update-index/prompts/init-explorer.md)"
   ```
3. For each discovered repo:
   - **If state is `NO_REMOTE` or `EMPTY_REMOTE`**, skip subagent dispatch. Write a minimal stub to `.update-index/scratch/<name>.entry.md`:
     ```
     ## <name>
     **Purpose:** (no remote / empty remote — not yet indexed)
     **Description:** This repo has no content on its remote yet. Re-run `/update-index --force` after content is pushed.
     **Domains:** -
     **Interacts with:** -
     **Start here:** -
     **Tech:** -
     **Recent substantial changes:**
     - -
     ```
     And an empty KG file at `.update-index/scratch/<name>.kg.txt` (or skip the KG paragraph).
   - **Otherwise**, dispatch an `Agent`:
     - `subagent_type`: `general-purpose`
     - `model`: `sonnet` (use `opus` only if the user explicitly flags a repo as complex)
     - `prompt`: the template with `{{REPO_NAME}}`, `{{REPO_PATH}}`, `{{ENTRY_SCRATCH_PATH}}`, `{{KG_SCRATCH_PATH}}` substituted.
   - **Dispatch all subagents in parallel** (single message, multiple `Agent` tool calls).

4. Wait for all agents to report. Interpret their reply:
   - `DONE <n>` → success; check that the scratch files exist.
   - `BLOCKED <reason>` → retry once with clearer scoping; if it blocks twice, emit a placeholder stub and move on.

5. Build the concept map: concatenate all `.update-index/scratch/<name>.kg.txt` files (with `## <name>` headers), substitute into the `kg-builder.md` prompt's `{{KG_PARAGRAPHS}}` placeholder, dispatch ONE subagent (`model: opus`). Write its response to `.update-index/scratch/concept-map.md`.

6. Assemble the index:
   ```
   bash ~/.claude/skills/update-index/scripts/assemble-index.sh <workspace>
   ```

7. Record the SHAs:
   ```
   for each repo: set_last_scanned_sha <workspace> <name> <sha>
   ```

8. Report to the user:
   `Init complete — N repos indexed, K concepts in map, <elapsed>.`

### Step 3b — Update mode

1. Source the lib. Load meta.json via `load_index_meta <workspace>`.

2. Partition repos:
   - **new** (on disk, not in meta): run init path for these; mark KG as needing recompute.
   - **removed** (in meta, not on disk): delete their scratch files; call `remove_repo_from_meta <workspace> <name>`; mark KG as needing recompute.
   - **unchanged** (current SHA == last SHA): no work.
   - **updated** (SHA changed): collect signals:
     ```
     bash ~/.claude/skills/update-index/scripts/collect-signals.sh <repo_path> <last_sha>
     ```
     - If exit 0 with no stdout → no meaningful signals → skip.
     - If signals produced → dispatch an update-evaluator subagent (`model: haiku`) with the prompt and signals.

3. For each evaluator returning `CHANGED`, overwrite the scratch entry and KG files; mark KG as needing recompute.

4. If the KG needs recompute (any change), re-run the kg-builder subagent using all current scratch KG files. Write to `concept-map.md`.

5. `bash assemble-index.sh <workspace>` → writes new `INDEX.md`.

6. Update meta.json with current SHAs for all repos.

7. Report: `Update complete — N new, M updated, K unchanged, <map regenerated? yes/no>.`

## Scratch preservation

The per-repo entry and KG files in `.update-index/scratch/` are the canonical
store. `INDEX.md` is assembled from them; it can be regenerated losslessly.
Do NOT delete scratch files except for removed repos.

## Performance expectations

- **Init** (~40–50 repos): 5–15 minutes, dominated by parallel subagent
  latency. Token cost is significant (each subagent reads files and
  generates a structured block + KG paragraph).
- **Update, no changes**: ~30 seconds — just discovery + signal collection,
  no subagent dispatch.
- **Update, some changes**: ~1–3 minutes, plus KG-builder if any repo
  changed.

## Non-goals

- No deep-code understanding. The skill is explicitly *scaffolding*.
- No automatic full-refresh schedule. User triggers with `--force`.
- No per-branch indexing. Index reflects the default-branch view only.
- `/update-repos --with-index` only *hints* at invoking this skill;
  it never runs silently as part of a pull.

## Related

- `/update-repos` — pulls the latest from the GitHub org. Run it before
  `/update-index` update mode so the index reflects freshly-pulled state.
