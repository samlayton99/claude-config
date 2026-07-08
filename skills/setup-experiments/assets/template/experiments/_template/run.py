#!/usr/bin/env python3
"""run.py — self-contained experiment script (template).

Copy this folder to experiments/expXNN_name/ to start a new experiment. This script:
  1. resolves the repo root by a FIXED parent depth (experiments are flat, so this is constant),
  2. loads this experiment's config.yaml,
  3. runs the experiment (expanding any sweeps),
  4. does its OWN analysis (no shared analysis module),
  5. saves metrics (JSONL) + the resolved config + figures to the mirrored results/ path.

Run: python experiments/expXNN_name/run.py
"""
import json
from pathlib import Path

import yaml

# ---- paths: repo root is a constant depth up; results mirror this experiment's folder ----
REPO_ROOT = Path(__file__).resolve().parents[2]          # experiments/expXNN_name/run.py -> repo root
EXP_DIR = Path(__file__).resolve().parent
# import shared pieces from the core library, e.g.:
# import sys; sys.path.insert(0, str(REPO_ROOT))
# from src.config import load_config, expand_sweep
# from src.data import build_dataset


def results_dir(cfg: dict) -> Path:
    """Mirror this experiment into results/, grouped by {{group}}."""
    group = f"{{group}}_{cfg['group']}_{cfg['group_name']}"  # e.g. {{group}}_A_numerics
    d = REPO_ROOT / "results" / group / EXP_DIR.name
    d.mkdir(parents=True, exist_ok=True)
    return d


def collect_data(cfg: dict) -> list[dict]:
    """Run the experiment; return a list of metric records (one per sweep cell / seed)."""
    records = []
    # for cell in expand_sweep(cfg):
    #     metric = ...                      # run it
    #     records.append({"cell": cell, "metric": metric})
    return records


def analyze_and_plot(records: list[dict], out: Path) -> None:
    """This script owns its analysis. Make figures from `records`; save to `out`."""
    # import matplotlib.pyplot as plt
    # legend OUTSIDE the axes, above the plot (see CLAUDE.md conventions)
    pass


def main() -> None:
    cfg = yaml.safe_load((EXP_DIR / "config.yaml").read_text())
    out = results_dir(cfg)

    records = collect_data(cfg)

    # save machine-readable outputs (so figures regenerate without recomputing)
    with (out / "metrics.jsonl").open("w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    (out / "config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))

    analyze_and_plot(records, out)
    print(f"wrote results to {out}")


if __name__ == "__main__":
    main()
