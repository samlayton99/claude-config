# skill_rules.md — how the dl-trainer skill operates

The operating directive. **SKILL.md** is the vision and the map (read it first, briefly);
**this file** is what you actually follow. Immutable: do not edit `rules/`, `scripts/`,
`scaffold/`, or `SKILL.md` while running the skill — you may only ever change `tasks/` and
`references/`, and only per `rules/update-guidance.md`.

Skill paths below are under **`~/.claude/skills/dl-trainer/`** (your working dir is the user's
project; the scaffolded workspace's `core/`/`experiments/` are relative to that project).

## The map — what lives where (all under `~/.claude/skills/dl-trainer/`)

| Folder | Mutable? | What it is |
|---|---|---|
| `scaffold/` | no | the training-workspace template copied into the user's repo (its own `AGENTS.md` governs it after copy) |
| `tasks/` | **yes** | one folder per task type: verified `config.yaml` hyperparameters + a `<task>.md` knowledge file. `tasks/tasks.md` is the index |
| `references/` | **yes** | `glossary.md` (training-loop mechanics & gotchas) + `runlog.md` (your retrospectives) |
| `rules/` | no | this file + `update-guidance.md` (how to grow the durable layer) |
| `scripts/` | no | `scaffold.py` (emits the workspace) + `check_reference.py` (validates `tasks/`) |

## Core philosophy

- **The curated `tasks/` library IS the answer — never reconstruct a config from memory alone.**
  If the task isn't in `tasks/`, research it to the adoption bar and add it (per
  `update-guidance.md`), or say you can't — don't guess SOTA.
- **The hierarchy is the asset; port, don't rebuild.** The scaffold's value is its *organization*
  (shared `core/`, thin `experiments/`, `results/` mirroring, the `config → run → results`
  contract), not the supervised loop it ships. Retarget `core/` to the task by **porting the best
  verified tool into it** (DeepXDE, CleanRL, FlashAttention, timm…) — never rebuild from scratch
  what a maintained implementation already does; rebuild only the component the research is about.
  Full statement in `SKILL.md` → "Port, don't rebuild".
- **Scaffold, then ADAPT.** The scaffold is a working reference workspace, not a framework to copy
  verbatim. Stand it up, then fit it to the task: seams + `config.yaml` for supervised-shaped
  tasks; a setup-time `core/` retarget (porting the recipe's tool) when the paradigm differs (PINN,
  RL, diffusion, LLM-pretrain). The experiment folder stays thin.
- **Grow knowledge conservatively; bias toward no change.** Better to lag a month than adopt
  something off-base. Anti-bloat is a feature.

## Workflow — called once at the start of a training project

1. **Identify the task type.** Read `tasks/tasks.md` (the live index — don't hardcode). If
   ambiguous, ask questions. Work hard to understand what the user is actually trying to do. 
   Genuine new task → step 6.
2. **Load the recipe.** Read `tasks/<task>/<task>.md` and its `config.yaml`. That baseline IS
   the answer. Read `references/glossary.md` for the loop mechanics the scaffold encodes.
3. **Conservative currency check** (per `update-guidance.md`). A few directed searches: is the
   gold-standard repo still maintained and still the default? Anything overtaken it in
   *adoption* (not just benchmarks)? Bias hard toward not changing; only the most obvious changes 
   are adopted, unproven findings go on a watchlist, never into a config. Re-verify stale entries
   (`python ~/.claude/skills/dl-trainer/scripts/check_reference.py`).
4. **Scaffold, then retarget `core/` to the task.**
   `python ~/.claude/skills/dl-trainer/scripts/scaffold.py --dest <dir> --name <exp> --task <task>`
   (`--list-tasks` to see options) emits the workspace and seeds the first experiment with the
   task's verified hyperparameters. Then decide how far `core/` must move:
   - **Paradigm matches the supervised default** (image classification, finetuning, most
     audio/ASR): keep `core/` as-is; customize the first experiment at the seams (`config.yaml` +
     `experiment.py`). The common path.
   - **Paradigm differs** (PINN, RL, diffusion, self-supervised / LLM-pretrain, neural-operator,
     self-play): **retarget `core/` at setup** so the task's native loop lives in the shared layer
     — by **porting the recipe's verified tool into `core/`**, not reconstructing it (host DeepXDE
     in `core/solve.py`; vendor CleanRL's `ppo.py` into `core/train.py`, update-math byte-identical).
     Flexible core is allowed here: add files (`core/solve.py`, `core/env.py`, `core/problem.py`)
     and deps. The experiment folder stays thin (ideally `config.yaml` only). **Match the user's
     intent:** bias to porting, but the component the research is *about* (a novel architecture, a
     never-done training loop) is built deliberately — port everything around it, rebuild that.
   Either way, **preserve the reproducibility contract** — config-driven, writes
   `results/<exp>/run_*/` through `utilities/tracking`, resumable where the paradigm allows;
   override the hardware auto-pick when the paradigm demands it (PINNs need float64; Apple-MPS
   can't, so pin CPU). Then **trim the supervised-only pieces the retarget makes dead**
   (`sanity.py`'s overfit gate, the `(X,y)` dataloader, launchers nothing runs) — *obvious*
   non-use only; if unsure something is reachable, keep it. Some paradigms legitimately drop a feature
   that can't fit (DeepXDE's L-BFGS owns its stopping → single-run resume N/A; sweep still applies) —
   don't force it. Don't edit `core/` *per experiment* once it's fitted. `AGENTS.md` is the contract.
5. **Verify before training (proof, not assertion).** Have the user run `uv sync`, then
   `uv run python -m utilities.hardware` and `uv run python -m core.run experiments/<exp>`. The
   loop runs the **sanity gate** first — a failure there is a real setup bug, fix it before a
   real run.
6. **(New task only) Extend the library.** Research to the adoption bar, then add a
   `tasks/<task>/` folder (copy `tasks/_template/`) with `config.yaml` (+ `_recipe`) and
   `<task>.md`, register it in `tasks/tasks.md`, per `update-guidance.md`. Run
   `python ~/.claude/skills/dl-trainer/scripts/check_reference.py`.
7. **Retrospective** (after many real runs). Append to `references/runlog.md`: task, resolved
   config, what worked/didn't, error→fix. Most runs are noise — log only the aha moments (a real
   insight, a better hyperparameter, a fixed bug); recurring findings can later justify a config
   change.

## Hard invariants

- Never reconstruct a config from memory; use `tasks/` as a reference or research-and-add it.
- Every `tasks/<task>/` needs `config.yaml` (with `_recipe`: summary, source, last_verified,
  adoption) **and** a `<task>.md` with an evidence section + date. No exceptions.
- A new/unknown task = a new `tasks/<task>/` folder — never a guess inlined into a project.
- Only `tasks/` and `references/` change. Editing `rules/`, `scripts/`, `scaffold/`, or
  `SKILL.md` is out of bounds for the self-update process.
- After any change to the durable layer, `~/.claude/skills/dl-trainer/scripts/check_reference.py`
  must pass (0 errors).
- **Existing projects, never blank-slate them.** Re-running the skill's `scaffold.py` on a populated repo is
  safe and idempotent — it skips existing files and never rewrites an experiment's `config.yaml`
  without `--force`. Do NOT pass `--force` to a project that holds real experiments/results, and
  never re-scaffold to "refresh" a user's work. To add to an existing project, create a *new*
  experiment folder (a free `NNN_name`); shared `core/` is only refreshed deliberately.
