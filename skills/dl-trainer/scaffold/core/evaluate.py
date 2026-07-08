"""core/evaluate.py — load a checkpoint and score it (reuses train.evaluate, so
there is one eval path, not two). Respects the experiment's overrides.

    python -m core.evaluate experiments/001_baseline             # latest run's best.pt
    python -m core.evaluate experiments/001_baseline --ckpt <path>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

from core.run import load_experiment
from core.train import evaluate
from data.dataloader import build_loaders
from utilities.hardware import pick_device


def _latest_ckpt(exp_name: str) -> str:
    """Most-recent run's best.pt under results/<exp_name>/. Sort by mtime, not name —
    non-datetime run dirs (e.g. a leftover run_smoke) must not sort ahead of real runs."""
    runs = sorted((Path("results") / exp_name).glob("run_*"), key=lambda p: p.stat().st_mtime)
    if not runs:
        sys.exit(f"no runs under results/{exp_name}/ — train it first, or pass --ckpt")
    return str(runs[-1] / "checkpoints" / "best.pt")


def main(exp_dir: str, ckpt_path: str | None):
    cfg, builders = load_experiment(exp_dir)
    ckpt_path = ckpt_path or _latest_ckpt(cfg["run"]["name"])
    device = pick_device(cfg["run"].get("device", "auto"))

    # Rebuild the model and load weights (strip any torch.compile prefix).
    model = builders["build_model"](cfg).to(device)
    ckpt = torch.load(ckpt_path, map_location=device)
    state = ckpt["model_state_dict"] if "model_state_dict" in ckpt else ckpt
    model.load_state_dict({k.replace("_orig_mod.", ""): v for k, v in state.items()})

    # Score it on the val set (fall back to train if there's no val split).
    train_ds, val_ds = builders["build_datasets"](cfg)
    ds = val_ds if val_ds is not None else train_ds
    _, loader, _ = build_loaders(cfg, ds, ds)
    metrics = evaluate(model, loader, builders["build_loss"](cfg), device, amp=False, amp_dtype=torch.float32)
    print({k: round(v, 4) for k, v in metrics.items()})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("experiment", help="path to an experiments/<name> folder")
    ap.add_argument("--ckpt", default=None, help="checkpoint (default: results/<name>/best.pt)")
    a = ap.parse_args()
    main(a.experiment, a.ckpt)
