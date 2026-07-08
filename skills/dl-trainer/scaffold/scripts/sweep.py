"""sweep.py — grid + seed sweep for ONE experiment.

Each trial (one hyperparameter combo × one seed) is a full run written to
results/<exp>/sweep_<ts>/run_<NNN>/ (same layout as a single run). swept_parameters.json
records which params each run_NNN used; sweep.log tracks orchestration (done / failed /
skipped). A trial whose summary.json already exists is SKIPPED — a dead sweep resumes
cheaply, and you never recompute (aggregate across seeds afterward from the saved data).

Backend: **gpusweep** (Roberto09/runner) is the default and is excellent — it packs trials
across all visible GPUs in parallel and handles scheduling cleanly. It's ON whenever it's
installed (`uv sync --extra sweep`). If it isn't installed — or you pass `--sequential` — the
sweep falls back to running trials one at a time with **no extra dependencies**: same trials,
same outputs, just no parallel GPU scheduling. So you can leave the sweep extra out and this
still works; add it when you want the speed.

    python scripts/sweep.py experiments/001_baseline [--sequential]
"""
from __future__ import annotations

import copy
import itertools
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # workspace root on path
from core.run import experiment_key, load_experiment
from core.train import train_once

# gpusweep is optional — present it as the default, degrade gracefully without it.
try:
    from pydrafig import pydraclass
    from gpusweep.configs.base_experiment_config import BaseExperimentConfig
    from gpusweep.configs.search_configs import GridSearchConfig
    from gpusweep.gpu_utils import GPUJobResult
    from gpusweep.grid_search import run_grid_searches
    HAVE_GPUSWEEP = True
except ImportError:
    HAVE_GPUSWEEP = False

# Passed via env so gpusweep subprocesses inherit them.
EXP_DIR = os.environ.get("DL_EXPERIMENT", "experiments/_template")
SWEEP_DIR = os.environ.get("DL_SWEEP_DIR", "")

# short sweep key -> dotted path in config.yaml
PARAM_TO_PATH = {"lr": "optim.lr", "weight_decay": "optim.weight_decay",
                 "batch_size": "data.batch_size", "seed": "run.seed"}


###############################################################################
################################### Helpers ###################################
###############################################################################

def _set_dotted(d, dotted, value):
    """Set a nested key by dotted path, e.g. 'optim.lr' -> d['optim']['lr']."""
    keys = dotted.split(".")
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value


def _run_name(idx): return f"run_{idx:03d}"


def _log(msg):
    """Print + append to the sweep's orchestration log."""
    line = f"{datetime.now():%H:%M:%S}  {msg}"
    print(line)
    if SWEEP_DIR:
        with open(Path(SWEEP_DIR) / "sweep.log", "a") as f:
            f.write(line + "\n")


def run_trial(idx, overrides):
    """Run ONE trial into SWEEP_DIR/run_<idx> and return its best metric. Shared by both
    backends. Idempotent: a trial whose summary.json exists is skipped (cheap resume)."""
    run_dir = Path(SWEEP_DIR) / _run_name(idx)
    if (run_dir / "summary.json").exists():
        _log(f"{_run_name(idx)} already done — skipped")
        return json.loads((run_dir / "summary.json").read_text()).get("best")

    # Load the experiment, apply this trial's overrides, point it at run_dir, train.
    cfg, builders = load_experiment(EXP_DIR)
    cfg = copy.deepcopy(cfg)
    for key, val in (overrides or {}).items():
        _set_dotted(cfg, PARAM_TO_PATH.get(key, key), val)
    cfg["run"]["dir"] = str(run_dir)
    try:
        best = train_once(cfg, **builders)["best"]
        _log(f"{_run_name(idx)} done  best={best:.4f}  {overrides}")
        return best
    except Exception as e:
        _log(f"{_run_name(idx)} FAILED  {overrides}  {e}")
        raise


###############################################################################
########################### Trial config (gpusweep) ###########################
###############################################################################

# Defined only when gpusweep is installed; the sequential path doesn't need these.
if HAVE_GPUSWEEP:

    @pydraclass
    class TrialConfig(BaseExperimentConfig):
        overrides: dict | None = None      # short-key -> value for this trial
        trial_idx: int = 0

    @pydraclass
    class TrialSearchConfig(GridSearchConfig):
        overrides: dict | None = None
        trial_idx: int = 0

        def get_experiment_config_and_base_dir(self, **_):
            base_dir = str(Path(SWEEP_DIR) / _run_name(self.trial_idx))
            cfg = TrialConfig(overrides=self.overrides or {}, trial_idx=self.trial_idx, base_dir=base_dir)
            cfg.finalize()
            return cfg, base_dir

        def run_experiment_config(self, config: TrialConfig):
            return run_trial(config.trial_idx, config.overrides)

        def agg_results(self, results: list[GPUJobResult]):
            ok = [r.result for r in results if r.success and r.result is not None]
            return float(np.mean(ok)) if ok else None


###############################################################################
################################# Entry point #################################
###############################################################################

if __name__ == "__main__":

    # Args: the experiment path, and an optional --sequential to force the no-dep backend.
    sequential = "--sequential" in sys.argv
    positional = [a for a in sys.argv[1:] if not a.startswith("-")]
    EXP_DIR = positional[0] if positional else EXP_DIR
    os.environ["DL_EXPERIMENT"] = EXP_DIR

    # Fresh datetime-stamped sweep dir (shared with subprocesses via env).
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    SWEEP_DIR = str(Path("results") / experiment_key(EXP_DIR) / f"sweep_{ts}")
    os.environ["DL_SWEEP_DIR"] = SWEEP_DIR
    Path(SWEEP_DIR).mkdir(parents=True, exist_ok=True)

    # ── edit your search here ──
    SEARCH_SPACE = {"lr": [3e-4, 1e-3, 3e-3], "weight_decay": [0.0, 0.1]}
    SEEDS = [42, 43]

    # Enumerate trials = combos × seeds -> run_000, run_001, ...  and record the map.
    keys = list(SEARCH_SPACE)
    trials, mapping = [], {}
    for i, (combo, seed) in enumerate(itertools.product(itertools.product(*SEARCH_SPACE.values()), SEEDS)):
        params = dict(zip(keys, combo)); params["seed"] = seed
        trials.append((i, params)); mapping[_run_name(i)] = params
    (Path(SWEEP_DIR) / "swept_parameters.json").write_text(
        json.dumps({"search_space": SEARCH_SPACE, "seeds": SEEDS, "runs": mapping}, indent=2))

    # Pick the backend: gpusweep (parallel, default when installed) unless forced sequential.
    use_gpusweep = HAVE_GPUSWEEP and not sequential
    _log(f"sweep start — {len(trials)} trials -> {SWEEP_DIR}  "
         f"(backend: {'gpusweep (parallel)' if use_gpusweep else 'sequential'})")

    if use_gpusweep:
        # gpusweep schedules every trial across all visible GPUs (slurm sets CUDA_VISIBLE_DEVICES).
        configs = [TrialSearchConfig(base_dir=str(Path(SWEEP_DIR) / _run_name(i)), overrides=params,
                                     trial_idx=i, sweep_props=None, base_experiment_config=None)
                   for i, params in trials]
        run_grid_searches(configs, max_gpus=max(1, torch.cuda.device_count()), simultaneous_jobs_per_gpu=1)
    else:
        # Dependency-free fallback: run trials one at a time; keep going if one fails.
        if not HAVE_GPUSWEEP and not sequential:
            _log("gpusweep not installed — running sequentially (uv sync --extra sweep for parallel GPU scheduling)")
        for i, params in trials:
            try:
                run_trial(i, params)
            except Exception:
                pass   # already logged; a failed trial shouldn't kill the sweep

    _log("sweep done")
    print(f"results under {SWEEP_DIR}/  (swept_parameters.json maps run_### -> params)")
