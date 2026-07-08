"""fit_finder.py — binary-search the largest batch size that trains without OOM,
for one experiment.

Built on gpusweep's binary search. Probes a few steps at a candidate batch size;
on OOM train_once raises and the trial is marked "doesn't fit", so the search moves
smaller. `success_direction_lower=False` means: on a fit, try larger.

GPU-only (no OOM to detect on CPU). Run:
    python utilities/fit_finder.py experiments/001_baseline

Requires the sweep extra:  uv sync --extra sweep  (installs gpusweep).
"""
from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # workspace root on path
from core.run import experiment_key, load_experiment
from core.train import train_once

from pydrafig import pydraclass
from gpusweep.binary_search import run_binary_searches
from gpusweep.configs.base_experiment_config import BaseExperimentConfig
from gpusweep.configs.search_configs import BinarySearchConfig
from gpusweep.gpu_utils import GPUJobResult

EXP_DIR = os.environ.get("DL_EXPERIMENT", "experiments/_template")
PROBE_STEPS = 3        # train this many steps; surviving them == "fits"


###############################################################################
################################ Search config ################################
###############################################################################

@pydraclass
class FitExperimentConfig(BaseExperimentConfig):
    batch_size: int = 64


@pydraclass
class FitBinarySearchConfig(BinarySearchConfig):

    def get_experiment_config_and_base_dir(self, batch_size, **_):
        bs = int(batch_size)
        base_dir = f"{self.base_dir}/bs_{bs}"
        cfg = FitExperimentConfig(batch_size=bs, base_dir=base_dir)
        cfg.finalize()
        return cfg, base_dir

    def run_experiment_config(self, config: FitExperimentConfig):
        # Load the experiment, force a tiny probe run at this candidate batch size.
        bs = int(config.batch_size)
        cfg, builders = load_experiment(EXP_DIR)
        cfg = copy.deepcopy(cfg)
        cfg["data"]["batch_size"] = bs
        cfg["train"]["epochs"] = 1
        cfg["train"]["max_steps"] = PROBE_STEPS    # just probe; train honors this
        cfg["train"]["sanity_gate"] = False
        cfg.setdefault("logging", {})["wandb"] = False
        cfg["run"]["dir"] = f"results/{experiment_key(EXP_DIR)}/fit_finder/bs_{bs}"
        train_once(cfg, **builders)                # OOM here raises -> trial fails -> "doesn't fit"
        return bs

    def agg_results(self, results: list[GPUJobResult]):
        ok = [r for r in results if r.success]
        return (len(ok) > 0, ok[0].result if ok else None)   # (fits?, batch_size)


###############################################################################
################################# Entry point #################################
###############################################################################

if __name__ == "__main__":
    EXP_DIR = sys.argv[1] if len(sys.argv) > 1 else EXP_DIR
    os.environ["DL_EXPERIMENT"] = EXP_DIR
    search = FitBinarySearchConfig(
        base_dir=f"results/{experiment_key(EXP_DIR)}/fit_finder",
        prop="batch_size",
        range=(8, 4096),               # search window for batch size
        precision=8,                   # stop when the window is < 8
        success_direction_lower=False, # on a fit, try LARGER
        sweep_props=None,
        base_experiment_config=FitExperimentConfig(),
    )
    run_binary_searches([search], max_gpus=1, simultaneous_jobs_per_gpu=1)
    print("fit_finder done — largest fitting batch size reported above.")
