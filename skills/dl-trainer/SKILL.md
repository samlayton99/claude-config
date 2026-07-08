---
name: dl-trainer
description: >-
  Set up a sensible, reproducible deep-learning training environment for a
  specific task, using community-verified gold-standard configs. Use when the
  user wants to start a new training project, scaffold a PyTorch training loop,
  "set up training", "train a model" (LLM/transformer, computer vision, audio/
  speech/ASR, scientific ML/PINN/neural-operator, RL/AlphaZero self-play, etc...),
  pick optimizer/LR/schedule/batch hyperparameters, or get an out-of-the-box DL
  experiment workspace (core/ train loop + model + optimization, experiments/ folders,
  config.yaml, data/, results/, slurm/sweep). Also use to research the current
  best-practice setup for a DL task, or to update/extend this skill's task library.
  Triggers: "set up a training run", "scaffold a deep learning project",
  "what hyperparameters for this task", "train an LLM/ViT/Whisper/PINN/RL agent".
---

# dl-trainer

Stand up a correct, reproducible **training workspace** for the user's task, with
**community-verified hyperparameters and training regime** — not guessed SOTA. Call 
it once at the start of a training project and you're set up to grow many experiments 
without the codebase rotting.

## Three primary value adds for the user 

1. Provide a repository of SOTA details (architectures, loss functions, hyperparameters, etc.)
for different deep learning tasks, easily referenced by agents.
2. Set up and adapt a well-organized dl repo environment for any task, equipped with useful tools
3. Automatically stay on top of the frontier and recent SOTA of corresponding tasks.

## The ideal outcome of invoking the skill

- A working experiment workspace copied into the user's repo — a shared `core/` training loop
  plus an adaptable first experiment, correct-by-construction (sanity gate, AMP, DDP, resume,
  sweeps), that runs the same on a laptop or an 8×GPU node.
- The **right hyperparameters** for the task, pulled from a curated, provenance-stamped library.
- A structure that stays organized as it grows (the workspace's `AGENTS.md` is its contract).
- The skill's knowledge-base automatically updated with the SOTA when deemed appropriate.

## Why it works

The skill's value is its **curated knowledge**, not Claude improvising. Two layers:

- **Knowledge** (`tasks/`, `references/`) — verified per-task hyperparameters + recipes, and
  the training-loop mechanics. Provenance-stamped; grown conservatively.
- **The scaffold** (`scaffold/`) — a working workspace template, *adapted* to the task, never
  copied verbatim.

## Core principle — adapt to the task and port what you can

The scaffold **hierarchy** is more important the training loop itself. The durable value is the organization:
a shared `core/` layer, thin `experiments/` (config, plotting, sweeps, analysis), `results/`
mirroring, and the `config → run → result-files` contract. The supervised loop in `core/` is a
*starting point*, not a fixture.

At project setup, retarget `core/` to the task by either building or **porting the best, most appropriate tools into it** 
— never rebuild from scratch what a maintained, verified implementation already does well. Priority: 
**port a verified library → vendor & adapt a reference implementation → write it yourself**. 
If truly nothing good exists, *or the research is about that component*: that's when you rebuild from scratch.

- Reuse a prebuilt attention stack with **FlashAttention** (`scaled_dot_product_attention` / HF
  Transformers) — hand-write attention only when the experiment *is* a novel-attention study.
- Don't reimplement a **cosine LR schedule**, AdamW, GAE, or AMP — import them.
- PINNs: **import DeepXDE** (it owns the autograd residual + Adam→L-BFGS); host it through
  `core/solve.py`, don't hand-roll the solver.
- RL: **vendor a benchmarked reference** (CleanRL's single-file PPO) into `core/`, update-math
  byte-identical; don't reconstruct PPO from memory.

The training loop/solver lives in `core/` (shared, reused by every experiment); the experiment folder stays
thin — ideally just `config.yaml`. Porting through `core/` keeps **both** the library's correctness
**and** the harness's reproducibility (manifest, metrics, checkpoints, sweeps) — bypassing to a
standalone script throws the latter away; rebuilding from memory throws the former away. 
**Match the build to the research:** bias to porting, but build the one component the work is 
genuinely investigating, and port everything around it.

**Caveat:** always verify that imports and tools are up to date (reference versions are often stale)

## Navigate this skill

Paths below are under the skill root **`~/.claude/skills/dl-trainer/`** (your working dir is the user's project).

**→ Read `~/.claude/skills/dl-trainer/rules/skill_rules.md` first — it is the operating
directive**: the map, the philosophy, and the step-by-step workflow. Everything else hangs off it.

| You want… | Read (under `~/.claude/skills/dl-trainer/`) |
|---|---|
| **how to run the skill** (workflow + rules) | **`rules/skill_rules.md`** ← start here |
| the per-task recipe + best-default hyperparameters | `tasks/tasks.md` → `tasks/<task>/` |
| how to research, verify, and grow the library | `rules/update-guidance.md` |
| training-loop mechanics, gotchas, sanity checks, general dl-knowledge | `references/glossary.md` |
| retrospectives from past runs | `references/runlog.md` |
| emit the workspace / validate the library | `scripts/scaffold.py` · `scripts/check_reference.py` |

One line to begin: `python ~/.claude/skills/dl-trainer/scripts/scaffold.py --dest <dir> --name
<exp> --task <task>` (`--list-tasks` to see the library) — then adapt the first experiment and run
the sanity gate. Follow `~/.claude/skills/dl-trainer/rules/skill_rules.md` for the full workflow.

GO TO "skill_rules.md" TO ACTUALLY START THE SKILL.