# AGENTS.md — house rules for this training workspace

You are to build and experiment with the user in their deep learning task. Follow the scaffold and
file structure given here so the repo's experiments and iterations grow in a maintainable and 
organized way.

## The one idea

- **`core/ utilities/ data/` are the shared layer.** You reuse them; *after setup* they grow only
  by *promotion* (see below) — never casual per-run edits, and rarely new files. (At
  project **setup**, `core/` is retargeted to the task's paradigm and MAY gain files/deps — see
  "Port, don't rebuild". Once fitted it's more or less stable: the supervised default keeps its five — evaluate,
  model, optimization, run, train — and `utilities/`/`data/` keep theirs.)
- **`experiments/<name>/` is where most new work goes.** Each experiment is self-contained
  and reuses the shared code, so one experiment is designed to never break another.
- **`results/` mirrors `experiments/`.** Outputs land at the experiment's *same path* under
  `results/` — `experiments/idea_xyz/exp01` → `results/idea_xyz/exp01/`. Subfolders are
  preserved automatically (the run dir is derived from the experiment path); nothing else writes there.

A new idea or one-off analysis = a **new experiment folder** (copy `experiments/_template`); a
*sweep over model variants* is still one folder (a registry in its `experiment.py`). Never a new
top-level file; edit `core/` only to **promote** likely reusable code (below), never "just for this run."

## Port, don't rebuild

The file structure and experiment tends to be more of an asset than training loop itself. At project 
setup, `core/` is usually retargeted to the task by *importing the best, most appropriate tool into it* first 
— import DeepXDE, vendor CleanRL's PPO, use FlashAttention / a cosine schedule from the library — rather
than rebuilding from scratch what a maintained implementation already does well. Lean toward
building only the component the research is actually about, and importing what surrounds it. The
ported training loop/solver lives in `core/` (shared); the experiment typically stays thin (ideally `config.yaml`).
This is a setup-time move — once `core/` is fitted, the rules below govern (growth lives in
`experiments/`, promote into the shared layer on reuse).

## Where things go

| Want to… | Do this |
|---|---|
| change hyperparameters | edit that experiment's `config.yaml` |
| use a custom model / data / loss / optimizer for one run | add `build_model` / `build_datasets` / `build_loss` / `build_optimizer` in that experiment's `experiment.py` |
| sweep many model variants | one experiment; a registry in its `experiment.py` (or `core.model.MODELS`), sweep `model.name` |
| reuse a model/loss/optimizer across experiments | **promote** it into `core/` — model→`model.py` (`MODELS`), loss/optimizer→`optimization.py` (see *Promotion*) |
| run a one-off analysis (probe, Hessian, plot) | a script *inside* `experiments/<name>/` (see "Analysis experiments" below) |
| add a genuinely shared, reusable capability | edit `core/` — must be very deliberate, affects every experiment, keep it backward-compatible |
| store a dataset | `data/raw/` (gitignored) |

## Promotion — start local, share when proven

Code earns its way into the shared layer; it doesn't start there. Use judgment — these are the
defaults, not a cage.

- **Local first.** A new model / loss / optimizer lives in an experiment's `experiment.py`
  (override `build_model` / `build_loss` / `build_optimizer`, or register a model into
  `core.model.MODELS`). Typically won't pre-seed `core/`.
- **Promote on reuse** : when a second experiment wants it and it's stable, move
  it into the existing shared file — model → `core/model.py` (add to `MODELS`), loss/optimizer →
  `core/optimization.py`. Keep it backward-compatible.
- **Promotion is churn-free** because selection is by name: the class moves, every experiment's
  `config.yaml` (`model.name: …`) is unchanged, and they all keep working. Experiments **import**
  shared pieces from `core/` (e.g. `from core.model import MLP`) — never copy them.
- **No new files** — promotion usually grows the existing files; try to keep `core/` to its five. New *directions*
  are new experiment folders, not new top-level files.
- **When in doubt, stay local.** One-off / bespoke glue → leave it in `experiment.py`. Only
  genuinely reusable pieces graduate.

## Hard rules

1. **Growth mostly lives in `experiments/`.** No top-level files/dirs, no `model_v2.py`. (Exception:
   the one-time setup retarget of `core/` to the task's paradigm — see "Port, don't rebuild".)
2. **Customize via `config.yaml` + `experiment.py`, not by editing `core/`.** Touch `core/`
   only to **promote** proven-reusable code (see *Promotion*) or a real shared improvement —
   backward-compatibly.
3. **All tunables live in `config.yaml`**, read via `cfg[...]`. NO HARDCODED HYPERPARAMETERS or constants/paths.
4. **Outputs → `results/<name>/`; raw data → `data/raw/`.** Never commit data or bloating results. (figures are fine)
5. **Keep the sanity gate on for supervised training.** If it flags something, fix the setup.
   Tasks that compute their own loss or have a stochastic objective (diffusion, some RL) can't
   overfit one batch — set `train.sanity_gate: false` there and rely on grad-flow (see *Adapting*).
6. **Reuse, don't copy.** Import shared pieces; never duplicate the loop or utilities.
7. **One experiment = one coherent thing** (one model family / one question). Different
   task → new experiment.

## Code style — write it scannable

Code here should read top-to-bottom like a **narrated outline**: a reader grasps a
file by skimming only its `#` headers, never having to parse the code to navigate it.
`core/train.py` is the reference. Match it when you add or edit code.

- **Layer the structure.** `####` hash boxes mark major movements; `# ---- name ----`
  marks sub-sections within a long function; a single `#` line heads each block.
  Small / config-ish files (`model.py`, a short `experiment.py`) need none of this —
  don't force banners onto 30 lines.
- **One block = one idea.** A blank line, a one-line `#` header that says what the
  next few lines do, then ~4–6 lines. Keep it granular: if the header needs an "and",
  split it into two blocks. `#` should appear even at the beginning of functions and 
  above most loops.
- **Spend vertical space on ideas, not syntax.** Pack argument lists, dict literals,
  and short `if cond: do()` onto as few lines as still read cleanly. No lonely `)`
  lines, no one-key-per-line dicts. The newlines you save go into separating ideas.
- **Comments say *why*, not *what*.** Flag the gotcha ("optimizer after model is on
  device"), not the obvious ("loop over the batches").
- **Extract construction & bookkeeping into named helpers** (`wrap_model`,
  `resume_from_checkpoint`) so the main flow stays a clean narrative — but keep
  control-flow *sequencing* inline. Don't hide the loop behind callbacks/wrappers;
  a reader should follow what-runs-when without jumping between files.

## Run it

```
uv sync
uv run python -m utilities.hardware                  # check device / precision
uv run python -m core.run experiments/<name>         # train (runs the sanity gate first)
uv run python -m core.evaluate experiments/<name>    # score the best checkpoint
NPROC=8 ./scripts/run.sh experiments/<name>          # multi-GPU (DDP)
sbatch scripts/train.slurm experiments/<name>        # cluster
```

## Results, logs & sweeps

Every run mirrors its experiment's path into `results/`, datetime-stamped, never
clobbered. `<name>` below = the experiment's path under `experiments/` (so
`experiments/idea_xyz/exp01` writes to `results/idea_xyz/exp01/` — nesting preserved,
no leaf-name collisions). This is automatic; you never set output paths by hand:

```
results/<name>/
  run_<datetime>/                 # one single run
    manifest.json                 # repro card (versions, seed, git SHA, resolved config)
    summary.json                  # final key metrics (best, final, wall-clock)
    metrics.jsonl                 # per-step/epoch records (append-only, machine-readable)
    checkpoints/  best.pt last.pt epochNNNN.pt
    logs/         train.log       # clean timestamped log (tqdm bar stays on the console)
    figures/                      # plots — written by analysis, NOT by training
  sweep_<datetime>/               # one sweep (scripts/sweep.py)
    swept_parameters.json         # run_### -> the exact params it used
    sweep.log                     # orchestration: each trial done / failed / skipped
    run_000/ run_001/ ...         # each trial = a full run folder (as above)
```

- **Don't recompute.** Figures are regenerated from `metrics.jsonl` / checkpoints —
  never retrain just to replot. A sweep **skips** any `run_###` whose `summary.json`
  already exists, so an interrupted sweep resumes cheaply.
- **Resume a single run:** `python -m core.run experiments/<name> --resume results/<name>/run_<datetime>`.
- **Logging:** use the run's logger / `metrics.jsonl` (via `utilities/tracking.py`); don't
  `print()` raw training output. Console shows a clean tqdm bar; `logs/train.log` stays uncluttered.
- `results/` is gitignored. Never commit it.

## Driving this workspace from a research loop

An external optimizer / research loop drives this workspace through one stable contract —
*write a config → run the CLI → read the result files* — and stays decoupled: it operates ON the
repo, never re-scaffolding or patching `core/`.

- **One trial = one experiment folder.** Write `experiments/<id>/config.yaml` (copy
  `experiments/_template`), then launch `python -m core.run experiments/<id>`.
- **Read the artifacts, not the logs.** Pick the next config from `summary.json` / `metrics.jsonl`
  / `manifest.json`; `logs/train.log` is for humans.
- **Restart-safe, one driver.** A finished trial (has `summary.json`) is skipped, so the loop
  resumes cheaply — just don't also run `scripts/sweep.py` against the space the loop owns.

## Cluster & scale (slurm)

- **Single run, multi-GPU one node:** `sbatch scripts/train.slurm experiments/<name>` —
  it launches `torchrun` with one process per GPU on the node (`hardware.py` wires DDP
  from the env, no code change 1→N GPUs).
- **Sweep on a cluster:** `sbatch` a job that runs `scripts/sweep.py experiments/<name>`
  inside a multi-GPU allocation; gpusweep schedules the trials across that allocation's
  GPUs. (There is no one-slurm-job-per-trial array by default — add one if you need
  thousands of trials.)
- **Multi-node is a fork point, not automatic.** `train.slurm` is single-node. For
  multi-node, use `--nodes=N`, one `torchrun` per node via `srun`, and a rendezvous
  (e.g. `c10d` on node 0) — adapt `train.slurm`; don't assume it already scales. Flag
  this as a deliberate change. FSDP / tensor-parallel are separate, bigger forks.
- **Step-based / streaming runs** (LLM, IterableDataset): the loop tolerates
  no-length loaders and fires eval+checkpoint on a step cadence — set
  `train.eval_every_steps` / `train.ckpt_every_steps` (epoch boundaries may never
  arrive). That works but stays epoch-*framed*: the tqdm bar is rebuilt each epoch and
  isn't step-budget-aware. For a real step-budget run, restructure the outer loop to
  step-first at setup — one `while global_step < max_steps` over an infinite iterator
  with a single `tqdm(total=max_steps)` bar — instead of bending the epoch loop.
  Reshaping `core/` at project setup is fine; per-experiment edits to it are not.

## Adapting to non-standard tasks

The core loop *as shipped* assumes supervised minibatches: `batch=(input,target)`,
`loss(output,target)`, accuracy-style eval. Once `core/` fits the task (it may have been
retargeted at setup — see "Port, don't rebuild"), customize per experiment at these seams in
`experiment.py`, never by branching `core/train.py`:

- **`build_loss`** — incl. the *model-computes-its-own-loss* case: have the model return the
  scalar loss and use an identity loss → `def build_loss(cfg): return lambda out, _: out`.
- **`build_datasets`** — your data (a streaming `IterableDataset` is fine; set `train.max_steps`).
- **`build_optimizer`** — e.g. layer-wise LR decay for finetuning
  (`timm.optim.create_optimizer_v2(model, "adamw", lr=..., layer_decay=0.8)`).
- **scoring** — when val-loss isn't meaningful (diffusion/RL), return `None` for the val dataset
  from `build_datasets` to skip the built-in eval, and score via your own analysis experiment.

For stochastic / self-supervised objectives, also set `train.sanity_gate: false` (the
overfit-one-batch check can't apply); grad-flow remains your correctness signal.

## Analysis experiments (not every experiment trains)

An experiment can be a one-off analysis (probe a checkpoint, compute a Hessian, plot).
Keep it contained to its folder and reuse shared code:

- Name it so its kind is obvious: `NNN_analyze_<thing>` (training runs are just `NNN_<name>`).
- A **training** experiment runs via `python -m core.run experiments/<name>`.
- An **analysis** script runs directly: `python experiments/<name>/analyze.py`. Because
  experiment folders start with a digit they aren't importable as modules, so put this
  two-line header at the top so `core`/`utilities`/`data` import cleanly:

      import sys, pathlib
      sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # workspace root

  Rebuild the model from the checkpoint's stored `config` (every checkpoint saves it) so
  the analysis stays in sync with how the run was defined.

## Scale-up knobs

Prefer turning these on when the setup supports them — low-cost wins: **AMP** (on by default),
**wandb** (`logging.wandb: true`), and **gpusweep** for parallel sweeps (`uv sync --extra sweep`;
`sweep.py` falls back to sequential without it). **DDP**, `torch.compile`, weight **EMA**
(`train.ema_decay`), and `scripts/sweep.py` / `utilities/fit_finder.py` are there for when you
scale up. If you don't use one, leave it in place — don't delete it to "tidy up" or expand it
casually. (Setup-time exception: if `core/` was retargeted to a different paradigm at setup — PINN,
RL, diffusion… — the skill may have already removed the supervised machinery that paradigm provably
can't reach; that one-time trim is done, this rule still holds for what remains.) Big forks (FSDP,
tensor/sequence parallel) are real decisions: flag them, don't smuggle them into the loop.

## About this file

A starting point, not a cage. If the project has genuinely evolved, keep the **spirit**
(shared core, contained growth, outputs out of the way) even where specifics changed —
don't be thrown by stale details. For recipes, hyperparameters, or new task types, consult
the **`dl-trainer` skill** at `~/.claude/skills/dl-trainer/`, which stays the source of truth.
