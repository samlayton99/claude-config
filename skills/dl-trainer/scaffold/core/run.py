"""core/run.py — compose an experiment with the shared loop. THE entry point.

    python -m core.run experiments/001_baseline      (or ./scripts/run.sh experiments/001_baseline)

Loads experiments/<name>/config.yaml, applies that folder's experiment.py overrides
(build_model / build_datasets / build_loss / build_optimizer) if present — else the
core defaults — runs core.train, and writes outputs to results/<name>/.

This is the seam that keeps growth directed: an experiment customizes by config +
its own experiment.py, never by editing core/ (which is retargeted only once, at
project setup — see AGENTS.md "Port, don't rebuild").
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from datetime import datetime
from pathlib import Path

import yaml

from core.model import build_model as _build_model
from core.optimization import build_loss as _build_loss, build_optimizer as _build_optimizer
from core.train import train_once
from data.dataloader import build_datasets as _build_datasets

OVERRIDABLE = ("build_model", "build_datasets", "build_loss", "build_optimizer")


###############################################################################
############################# Experiment loading ##############################
###############################################################################

def experiment_key(exp_dir) -> str:
    """The experiment's path *relative to experiments/* — the key results mirror.

    experiments/001_baseline        -> "001_baseline"      -> results/001_baseline/...
    experiments/idea_xyz/exp01      -> "idea_xyz/exp01"    -> results/idea_xyz/exp01/...
    So subfolders are preserved and two `exp01`s under different ideas never collide.
    Falls back to the leaf name if the path isn't under an `experiments/` dir."""
    parts = Path(exp_dir).parts
    if "experiments" in parts:
        i = len(parts) - 1 - parts[::-1].index("experiments")   # last 'experiments' segment
        return Path(*parts[i + 1:]).as_posix()
    return Path(exp_dir).name


def load_experiment(exp_dir):
    """Return (cfg, builders) for an experiment folder: its config.yaml plus any
    build_* overrides from its experiment.py (falling back to the core defaults)."""

    # Config: read config.yaml; name = path under experiments/ so results/ mirrors it.
    exp = Path(exp_dir)
    if not (exp / "config.yaml").exists():
        sys.exit(f"no config.yaml in {exp}  (copy experiments/_template to start one)")
    cfg = yaml.safe_load((exp / "config.yaml").read_text()) or {}
    cfg.setdefault("run", {})
    cfg["run"]["name"] = cfg["run"].get("name") or experiment_key(exp_dir)

    # Builders: core defaults, overridden by anything the experiment.py defines.
    builders = {"build_model": _build_model, "build_datasets": _build_datasets,
                "build_loss": _build_loss, "build_optimizer": _build_optimizer}
    exp_py = exp / "experiment.py"
    if exp_py.exists():
        spec = importlib.util.spec_from_file_location(f"experiment_{exp.name}", exp_py)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for name in OVERRIDABLE:
            if hasattr(mod, name):
                builders[name] = getattr(mod, name)
    return cfg, builders


###############################################################################
################################# Entry point #################################
###############################################################################

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("experiment", help="path to an experiments/<name> folder")
    ap.add_argument("--resume", default=None, help="continue an existing results/<name>/run_* dir")
    a = ap.parse_args()

    # Resolve the run directory: continue --resume, else a fresh datetime-stamped run.
    cfg, builders = load_experiment(a.experiment)
    if a.resume:
        cfg["run"]["dir"] = a.resume
    else:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        cfg["run"]["dir"] = str(Path("results") / cfg["run"]["name"] / f"run_{ts}")
    return train_once(cfg, **builders)


if __name__ == "__main__":
    main()
