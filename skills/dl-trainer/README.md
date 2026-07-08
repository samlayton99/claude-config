# dl-trainer

A Claude Code **skill** that stands up a correct, reproducible deep-learning training project
for your task — with **community-verified hyperparameters**, not guessed SOTA — and a clean
workspace built to grow many experiments without rotting.

You can ask Claude (e.g. *"set up training to finetune a Whisper model"* / *"scaffold a ConvNext image classifier"* / *"what hyperparameters for an LLM pretrain?"*) and it drives the skill for you. This README explains what you'll get and how to work with it.

## Install

This is a [Claude Code](https://claude.com/claude-code) skill. Install it by cloning into your Claude Code skills directory:

```bash
git clone https://github.com/samlayton99/dl-trainer ~/.claude/skills/dl-trainer
```

Claude Code auto-discovers skills in `~/.claude/skills/`. Start a new session and ask, e.g., *"set up training to finetune a Whisper model"*.

**Requirements:** Claude Code; Python 3.10+ with [`uv`](https://docs.astral.sh/uv/) (the generated workspace uses uv). The skill itself installs nothing else — per-task dependencies are pulled into the workspace on demand.

**For an agent installing this autonomously:** clone to *exactly* `~/.claude/skills/dl-trainer` — the skill's internal files reference that absolute path. If the directory already exists, back it up or remove it first. There is no build step and nothing to compile; installation is complete once the clone finishes. The library grows locally (new tasks, run-log entries) and is never expected to be pushed back upstream.

## What you get

When Claude runs the skill it:
1. **Identifies the task** from the curated library (`tasks/`).
2. **Loads the verified recipe** — the gold-standard models, losses, training tricks/traps, and
   the **best-default hyperparameters** for that task.
3. **Scaffolds a workspace** into your repo and seeds a first experiment with those
   hyperparameters merged in.
4. **Adapts that experiment** to your data/model, and runs a **sanity gate** before any real run.

The result is a self-contained training project you own and iterate on.

## The workspace (what lands in your repo)

```
<your project>/
  AGENTS.md            the workspace contract — read it; it keeps things clean as you grow
  pyproject.toml       uv environment (base is tiny; pull extras per task)
  core/                shared engine — the training loop, reused by every experiment
  utilities/           device/precision/DDP, the sanity gate, logging/metrics, batch-size finder
  data/                your Dataset + DataLoader (+ data/raw/ for files)
  experiments/         ALL your work — one folder per experiment (config.yaml + optional experiment.py)
  results/             outputs, datetime-stamped, mirroring experiments/ (gitignored)
```

**The model is the workflow:** shared `core/` stays stable; every new idea is a new
`experiments/<name>/` folder. You never edit `core/` for one run. Outputs land in
`results/<same path>/` automatically.

Run it (from the project root): `uv sync` then `uv run python -m core.run experiments/<name>`
(runs the sanity gate, then trains). The workspace's **`AGENTS.md`** has the full command set
(evaluate, multi-GPU/DDP, slurm), the `results/<name>/run_<datetime>/` layout, and `--resume`.

## Features

- **Correct-by-construction loop**: AMP (bf16/fp16), grad clip + accumulation, LR
  warmup+cosine/plateau, DDP (1→N GPUs, no code change), `torch.compile`, checkpoint/resume.
- **Sanity gate** runs first: loss-at-init, overfit-one-batch, gradient-flow — catches setup bugs
  before you burn a real run.
- **Weight EMA** (`train.ema_decay`), step-cadence eval/checkpoint for streaming/LLM runs, and
  graceful handling of length-less `IterableDataset`s.
- **Structured outputs** that automation can read; figures regenerate from `metrics.jsonl`
  (never retrain to replot).
- **Sweeps**: `scripts/sweep.py` does grid×seed search. It uses **gpusweep** (a well-built
  scheduler that packs trials across all visible GPUs in parallel) when installed
  (`uv sync --extra sweep`) — that's the default and recommended path — and otherwise falls back
  to running trials sequentially with no extra dependencies. `utilities/fit_finder.py` binary-
  searches the largest batch that fits.
- **uv** for a reproducible environment; the base install is deliberately small.

## Adapting & non-standard tasks

One experiment customizes via its `config.yaml` (all knobs) and an optional `experiment.py`
that overrides `build_model` / `build_datasets` / `build_loss` / `build_optimizer` (e.g.
layer-wise LR decay). Non-supervised or non-standard tasks (PINN, RL, diffusion, etc.) instead
retarget `core/` at setup by porting the verified tool into it — see the workspace `AGENTS.md`.

## How the knowledge stays trustworthy

The skill's value is its curated library, not improvisation. Each task carries provenance
(`source`, `last_verified`, `adoption`) and an evidence section. The skill **grows
conservatively**: on use it does a directed currency check, biases hard toward no change, and
stages unproven findings on a watchlist before they ever become a default. `scripts/
check_reference.py` validates freshness/provenance.

## Layout of this skill (for the curious / maintainers)

The skill is installed at **`~/.claude/skills/dl-trainer/`**; the paths below are relative to it.

- `SKILL.md` — the agent entry point (vision + map). `rules/skill_rules.md` — the operating
  directive (workflow + invariants). `rules/update-guidance.md` — how to grow the library.
- `tasks/` — the task library (`tasks.md` index + one folder per task). `references/` —
  `glossary.md` (loop mechanics) + `runlog.md` (your retrospectives).
- `scaffold/` — the workspace template. `scripts/` — `scaffold.py` (emit a project) +
  `check_reference.py` (validate the library).

To add a task type: copy `tasks/_template/`, fill `config.yaml` + `<task>.md`, add it to
`tasks/tasks.md`, run `python ~/.claude/skills/dl-trainer/scripts/check_reference.py`. (Claude
does this for you when you ask for a task it hasn't seen.)
