# Update guidance — how this skill's knowledge grows

This governs the **mutable layer only**: `tasks/` (per-task `config.yaml` + `<task>.md` +
`tasks.md` index) and `references/` (`glossary.md`, `runlog.md`). The self-update process may
edit these. It may **NEVER** edit `SKILL.md`, `rules/` (this file + `skill_rules.md`),
`scaffold/`, or `scripts/` — those are frozen.

Paths here are under the skill root **`~/.claude/skills/dl-trainer/`** (your working dir is the user's project).

The golden rule: **better to lag a month behind than to adopt something off base.** This
skill's value is a real, maintained, community-verified library — not Claude reconstructing
SOTA from memory. When in doubt, do nothing.

---

## The inclusion bar (community adoption, not recency)

A task config/recipe may enter `tasks/` ONLY if it clears the bar:

- **Stars / forks** — thousands of GitHub stars, actively maintained.
- **Citations** — hundreds-to-thousands for a method/paper.
- **Authorship** — credentialed authors / known labs (Karpathy, FAIR, Karniadakis, DeepMind,
  HuggingFace, …).
- **Forum / practitioner adoption** — it's what people actually reach for.

If it's new and flashy but unproven, it does **not** get a task folder or go into a recipe.
Note it under the **Watch** line in the relevant `<task>.md` Evidence section instead.

## The currency check (where live research earns its keep)

EVERY TIME the skill is invoked for a task, do a **directed** check — not a broad, open-ended 
discovery:

1. Read the existing `tasks/<task>/<task>.md` + `config.yaml`. That baseline is the answer
   unless there is strong evidence it's wrong.
2. Run a small number of targeted searches: "is `<gold-standard repo>` still maintained / still
   the default?" and "has anything overtaken it in adoption?"
3. **Bias hard toward no change.** Only propose an update if a candidate clearly clears the
   inclusion bar AND has displaced the incumbent in *adoption* (not just benchmark numbers).
4. If a search surfaces something promising but unproven, record it as a **Watch** line with a
   date; do not promote it unless it is totally obvious.

**No web access?** Then you can't run the currency check — do **not** bump `last_verified` (it
certifies a re-check against the *source*, not memory) and do **not** change any config value.
Use the existing baseline as-is. If you must add a brand-new task offline, stamp today's date but
add an explicit "unverified offline" caveat to its `<task>.md` Evidence section so the provenance
never looks stronger than it is.

## Staging (the conservatism mechanism)

Two tiers, both inside the task's `<task>.md`:

- **Gold standard** — promoted; its verified numbers live in that task's `config.yaml`.
- **Watch (not adopted)** — a line in the Evidence section: name, link, why it's interesting,
  date first seen. **Promotion requires a candidate to persist across at least two separate
  invocations spanning ~1 month AND to meet the inclusion bar.** Never let a Watch item skip
  straight into a `config.yaml`.

## Provenance & freshness (every task, no exceptions)

Every task carries, in `config.yaml`'s `_recipe` block AND its `<task>.md` Evidence section:

- `source:` primary URL(s) (repo / paper / official docs).
- `last_verified:` / _last updated:_ ISO date the numbers were confirmed against the source.
- `adoption:` the evidence (stars / citations / author).

`last_verified` is a **kill switch**: `scripts/check_reference.py` flags any task older than the
staleness budget (default 120 days). A stale entry is a liability — re-verify against the source
or leave it flagged; do not silently trust it.

## Adding a new task (gracefully, without redundancy)

1. **Check for overlap first.** Read `tasks/tasks.md` and the existing folders for one that
   subsumes the new task. Prefer extending an entry over a near-duplicate (e.g. "ViT finetune"
   belongs under `image_finetune`, not a new task).
2. Copy `tasks/_template/` to `tasks/<task>/`. Fill `config.yaml` (the verified hyperparameters
   + the `_recipe` block) and `<task>.md` (gold standard → recipe → evidence, with a date).
3. Add a row to the `tasks/tasks.md` index.
4. Run `scripts/check_reference.py`. Fix every ERROR; review WARNINGS.

The skill's router reads tasks dynamically from `tasks/tasks.md` + the folder names, so a new
task folder is auto-discoverable — no edit to `SKILL.md` (which is frozen) is needed or allowed.

## Growth management (prevent bloat)

- **Size budgets** (enforced by check_reference.py): SKILL.md ≤ 500 lines; each durable `*.md`
  ≤ 800. Keep `<task>.md` concise — scannable, not an essay.
- **One task folder per task type, not per experiment.** Per-run specifics go in `runlog.md`,
  never as new tasks.
- **Dedupe on write.** Two tasks with the same normalized summary or the same primary source is
  a smell — merge them. check_reference.py warns on this.
- **Prune conservatively.** Remove a task only when its source is dead (archived/unmaintained)
  AND a clearly-adopted replacement exists. Record the reason in `runlog.md`. When unsure, keep
  it and let it show as stale.

## The retrospective loop (compounding)

After a real run that gives meaningful information, append a summary to `references/runlog.md`: 
the task, the resolved config, what worked / what didn't, any error→fix. This is personal, 
hard-won data and is exempt from the community-adoption bar (it's YOUR result, not a claim about 
the field). Over time, recurring runlog findings can justify adjusting a task's `config.yaml` 
defaults — with a note pointing back to the runlog entries that motivated it.

## Before committing any self-update — checklist

- [ ] Change is to the mutable layer only (`tasks/`, `references/`) — not SKILL.md / rules /
      scaffold / scripts.
- [ ] New gold-standard entries clear the inclusion bar and have source + last_verified.
- [ ] No redundant task or duplicate config introduced.
- [ ] `scripts/check_reference.py` passes (0 errors).
- [ ] When the call was close, defaulted to NOT changing.
