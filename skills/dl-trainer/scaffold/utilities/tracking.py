"""tracking.py — logging, progress, and metrics recording for a run.

One clean place for the three "how do I see/save what happened" concerns:
  - setup_logging: a logger that prints clean lines to the console (without
    shattering a tqdm bar) AND to <run_dir>/logs/train.log.
  - progress: a tqdm bar on the main process, no-op elsewhere / if tqdm is absent.
  - Tracker: one sink, two backends — append machine-readable records to
    <run_dir>/metrics.jsonl AND mirror to W&B if logging.wandb is on; write a final
    <run_dir>/summary.json. Figures are regenerated from these — never retrain to replot.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

try:
    from tqdm.auto import tqdm
except Exception:  # tqdm is a base dep, but degrade gracefully if missing
    tqdm = None


###############################################################################
################################### Logging ###################################
###############################################################################

class _TqdmHandler(logging.Handler):
    """Emit log lines via tqdm.write so they don't break an active progress bar."""
    def emit(self, record):
        msg = self.format(record)
        (tqdm.write if tqdm is not None else print)(msg)


def setup_logging(log_dir, main_proc: bool = True):
    """Return a logger writing clean lines to the console (tqdm-safe) and to
    <log_dir>/train.log. Non-main DDP ranks get a silent logger."""
    logger = logging.getLogger("dl")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not main_proc:
        logger.addHandler(logging.NullHandler())
        return logger

    # Two handlers: tqdm-safe console + a plain file under the run's logs/.
    fmt = logging.Formatter("%(asctime)s  %(message)s", datefmt="%H:%M:%S")
    console = _TqdmHandler(); console.setFormatter(fmt); logger.addHandler(console)
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    fileh = logging.FileHandler(Path(log_dir) / "train.log"); fileh.setFormatter(fmt)
    logger.addHandler(fileh)
    return logger


###############################################################################
################################## Progress ###################################
###############################################################################

def progress(iterable, main_proc: bool = True, **kw):
    """tqdm bar on the main process; the bare iterable elsewhere or if tqdm absent."""
    if tqdm is None or not main_proc:
        return iterable
    kw.setdefault("leave", False)
    kw.setdefault("dynamic_ncols", True)
    return tqdm(iterable, **kw)


###############################################################################
############################### Metrics tracker ###############################
###############################################################################

def _init_wandb(cfg: dict, run_dir, resume_id=None):
    """Start a W&B run from the `logging:` block, or None if off/unavailable."""
    lg = cfg.get("logging") or {}
    if not lg.get("wandb", False):
        return None
    try:
        import wandb
    except ImportError:
        print("[wandb] not installed — skipping (uv add wandb)")
        return None
    return wandb.init(project=lg.get("project", "dl-trainer"), entity=lg.get("entity"),
                      name=cfg["run"]["name"], config=cfg, mode=lg.get("mode", "online"),
                      tags=lg.get("tags") or [], dir=str(run_dir),
                      id=resume_id, resume="allow" if resume_id else None)


class Tracker:
    """One metrics sink, two backends: always append to <run_dir>/metrics.jsonl, and
    mirror to Weights & Biases if logging.wandb is on. No-op on non-main ranks. JSONL
    is append-only + trivially parsable; analysis experiments read it to plot without
    retraining. Use one tracker.log(record) instead of writing each backend by hand."""

    def __init__(self, run_dir, cfg: dict, main_proc: bool = True, resume_id=None):
        self.enabled = main_proc
        self.run = _init_wandb(cfg, run_dir, resume_id) if main_proc else None
        if not main_proc:
            return
        self.dir = Path(run_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self._f = open(self.dir / "metrics.jsonl", "a")

    @property
    def wandb_id(self):
        return getattr(self.run, "id", None) if self.run is not None else None

    # Per-record logging: jsonl always, wandb mirror if on (drop the 'split' tag there).
    def log(self, record: dict, step: int | None = None):
        if not self.enabled:
            return
        self._f.write(json.dumps(record, default=str) + "\n")
        self._f.flush()
        if self.run is not None:
            self.run.log({k: v for k, v in record.items() if k != "split"}, step=step)

    # End-of-run summary: write summary.json + push scalar finals to the wandb summary.
    def summary(self, record: dict):
        if not self.enabled:
            return
        (self.dir / "summary.json").write_text(json.dumps(record, indent=2, default=str))
        if self.run is not None:
            self.run.summary.update({k: v for k, v in record.items() if isinstance(v, (int, float))})

    def finish(self):
        if not self.enabled:
            return
        self._f.close()
        if self.run is not None:
            self.run.finish()
