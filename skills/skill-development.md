# Skill development — the DL training/optimization stack

Three sibling skills. Each shares the same propose → evaluate → keep philosophy but
optimizes a different target. They compose; they do not duplicate.

## The stack

| Skill | Optimizes | Target artifact | Search method | Evaluation | Status |
|---|---|---|---|---|---|
| **dl-trainer** | *sets up* a training run | folder + `hyperparameters.yaml` | curated index lookup | sanity gate | built + validated |
| **autoresearch** | *improves* a training run | `train.py` code + numeric params | LLM greedy edits **+** classical HPO | held-out metric + budget floor | scaffold proposed |
| **gepa** | *improves* an LLM/agent pipeline | prompts / text artifacts | reflective Pareto evolution | scalar + textual trace feedback | proposed, not built |

Axis split: dl-trainer + autoresearch operate on **neural-net training**; gepa operates on
**text systems** (prompts/agents, no weight access). gepa is never called to train a net.

## Shared design principles (all three)

- **Hard boundary: durable curated knowledge vs. runtime work.** Real files on disk hold
  the configs/rules/templates; the model only fills gaps and checks currency. Never
  reconstruct from memory (the SkillsBench result is the spec, not a footnote).
- **Code does the deterministic work**, not the model (scaffolding, the loop harness, the
  sweep). The model proposes and judges; scripts execute and enforce.
- **Proof, not assertion.** A change is only "good" if a hardened evaluator confirms it on
  held-out data under an enforced budget. Resist reward-hacking with infrastructure, not
  prompts (the Gomoku/Crucible lesson).
- **Conservative growth.** Community-adoption bar, provenance + `last_verified` on every
  entry, staging/watchlist before promotion, size budgets, a `check_reference.py`-style
  health gate. Better to lag a month than adopt something off base.
- **Compounding memory.** A `runlog.md` captures what actually worked per run; recurring
  findings justify changing a default, with a pointer back to the evidence.

## Per-skill essence

### dl-trainer (built)
Stands up a correct, reproducible PyTorch project from a curated task→config index
(LLMs, vision, audio, scientific ML, RL). Frozen core = `SKILL.md` + `assets/scaffold/`
+ `scripts/`. Durable layer = `references/resources.md` (the index), `glossary.md` (the
training-loop knowledge), `update-guidance.md`, `assets/presets/*.yaml`. Emits the project
via `scripts/scaffold.py`; `train.py` runs a sanity gate first (loss-at-init, overfit-one-
batch, gradient-flow) and writes a repro `manifest.json`.

Baked-in dependencies (real code in the template, not external loops):
- **wandb** — on by default via the `logging:` block; `train.py` logs step/epoch metrics;
  no-ops if wandb is absent or `mode: disabled`.
- **gpusweep** (Roberto09/runner) — `sweep.py` (grid search, GPU-scheduled, seeds
  aggregated) and `fit_finder.py` (binary search for the largest batch that fits). The
  single-run `train.py` has no sweep dependency; it exposes `train_once(cfg)` which the
  sweep scripts call. This is the "runner is a library baked into the code" archetype —
  the opposite of autoresearch (a self-installing loop). Grid is for simple exhaustive
  sweeps; sample-efficient search (Optuna/CMA-ES) is the autoresearch skill's job.

### autoresearch (scaffold proposed)
The improvement loop over a project dl-trainer scaffolded. **Self-installing archetype:**
invoking the skill *copies its own markdown + scripts + `program.md` into the target repo*
(into the project's own folders), so the agent working in that repo has full local context
every time. The skill imports its contents in-place; it does not run from the skill dir.
This is the crucial difference from gpusweep: gpusweep is a *library* the template depends
on; autoresearch is a *loop* that materializes itself into the repo it operates on.

Karpathy's greedy edit→train→keep/revert loop + exactly **two** hybrid additions:
1. **Hardened evaluator** — keep only if a *held-out* metric improves and a *min-train-time
   floor* is cleared (anti-reward-hacking).
2. **Classical-HPO mode** — Optuna/CMA-ES for numeric params (beats LLM-as-optimizer in a
   fixed space).

Two modes mapped to triggers:
- `/autoresearch` → **Mode A (improve):** agent edits `train.py`, budgeted run, git keep/revert.
- `parameter tune this setup` → **Mode B (tune):** classical HPO sweep, writes best config back.

Reuses dl-trainer's `train.py`, sanity gate, and `runlog.md` (no duplication). dl-trainer
gains one optional hand-off line: "setup verified — want me to /autoresearch or tune it?"

Proposed layout:
```
autoresearch/
  SKILL.md                  frozen core: triggers, the two modes, loop rules, boundary
  scripts/autoresearch.py   Mode A driver: budgeted run -> held-out eval -> git keep/revert -> log
  scripts/hpo.py            Mode B: Optuna/CMA-ES multi-fidelity sweep over the config space
  scripts/evaluate.py       hardened evaluator (held-out metric + min-train-time floor)
  references/loop-guide.md  propose/keep/revert rules, "no ugly complexity / deletion is a win",
                            anti-reward-hacking rules, when to stop
  references/update-guidance.md  conservative growth (mirrors dl-trainer)
  assets/program.md         human-written "research direction" file, seeded into a project
  assets/runlog-entry.md    template appended to dl-trainer's runlog.md per accepted change
```
Deliberately omitted (future, documented not built): evolutionary/Pareto branching,
multi-GPU parallelism, multi-agent "chief scientist", cross-project memory.

### gepa (proposed, not built)
Optimizes text artifacts (prompts, instructions, agent configs) for LLM/agent pipelines via
reflective Pareto evolution. Inputs: a seed text artifact, a metric, a tiny dataset, a
reflection LLM. Uses scalar + **textual** trace feedback (richer signal than autoresearch's
scalar). Wraps DSPy's GEPA. Triggered when the thing being improved is a prompt/agent, not a
trained net. Same loop philosophy, different target and feedback channel.

## Why these are separate, not one mega-skill
Different boundaries, different durable knowledge, different evaluation. A small set of
focused skills beats one bloated document (SkillsBench). dl-trainer = setup; autoresearch =
training improvement; gepa = prompt/pipeline improvement.

## Open decisions (autoresearch)
- The two hybrid additions: held-out evaluator + classical-HPO mode — confirm or swap.
- Build gepa now, or design-only for now.
- Mode A autonomy: fully overnight unattended vs. checkpoint after every N kept changes.

## Sources (autoresearch research, June 2026)
- karpathy/autoresearch: https://github.com/karpathy/autoresearch (+ reward-hacking: discussions/322)
- Classical HPO beats LLM-as-optimizer in-space; hybrid ("Centaur") wins:
  https://krokotsch.eu/posts/autoresearch-hyperopt/ ; arXiv 2603.24647
- Evolution/Pareto/tree-search: AlphaEvolve (arXiv 2506.13131), AIDE, GEPA
- GEPA: https://github.com/gepa-ai/gepa ; https://dspy.ai/api/optimizers/GEPA/overview/
