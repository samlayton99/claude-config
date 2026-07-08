"""train.py — the shared training loop (core engine).

The reference loop every experiment reuses: correct op-ordering, AMP, clip, accum,
scheduler, sanity gate, checkpoint/resume, DDP (see references/glossary.md for the
why). At project SETUP this loop may be retargeted/replaced to the task's paradigm —
port the recipe's verified tool (see AGENTS.md "Port, don't rebuild"). Once fitted it
is stable: experiments customize via config + override hooks, not by forking this
file. Hardware/sanity live in utilities/.

Don't run this directly; the entry point is core/run.py:
  python -m core.run experiments/<name>        (or ./scripts/run.sh experiments/<name>)
"""
from __future__ import annotations

import json
import platform
import random
import subprocess
import time
from contextlib import nullcontext
from pathlib import Path

import numpy as np
import torch
from torch.nn.parallel import DistributedDataParallel as DDP

from data.dataloader import build_datasets, build_loaders
from core.model import build_model
from core.optimization import build_loss, build_optimizer, build_scheduler
from utilities import hardware as dev
from utilities import sanity
from utilities import tracking


###############################################################################
################################### Helpers ###################################
###############################################################################

def autocast_ctx(device, amp, amp_dtype):
    """AMP context for the active device, or a no-op when AMP is off (mps/cpu)."""
    return torch.autocast(device.type, dtype=amp_dtype) if amp else nullcontext()


def set_seed(seed: int):
    """Seed every independent RNG (torch, cuda, numpy, python)."""
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    # Determinism is opt-in (slower) — enable when reproducing exactly.
    # torch.backends.cudnn.deterministic = True; torch.backends.cudnn.benchmark = False


def to_device(batch, device):
    """Move a (input, target) batch onto the device, async where possible."""
    return [t.to(device, non_blocking=True) for t in batch]


def loader_len(loader):
    """len(loader) when the dataset is sized, else None — a DataLoader over a
    length-less IterableDataset *has* __len__ but raises when called (streaming)."""
    try:
        return len(loader)
    except TypeError:
        return None


def wrap_model(model, info, device, compile_model=False):
    """Move model to device, wrap in DDP under torchrun/srun, optionally compile.
    Returns (model_for_forward, raw_model); keep raw_model for optimizer/checkpoint."""
    raw_model = model.to(device)
    m = raw_model
    if info["distributed"] and device.type == "cuda":
        m = DDP(raw_model, device_ids=[info["local_rank"]])
    if compile_model:
        m = torch.compile(m)   # PyTorch 2.x; slow first step, then faster
    return m, raw_model


def resume_from_checkpoint(last_path, device, raw_model, optimizer, scheduler, scaler, ema=None):
    """Restore model/optimizer/scheduler/scaler (+ EMA) state from a checkpoint in
    place; return (best, global_step, start_epoch, wandb_id) to continue bookkeeping."""
    ckpt = torch.load(last_path, map_location=device)
    raw_model.load_state_dict({k.replace("_orig_mod.", ""): v for k, v in ckpt["model_state_dict"].items()})
    if ckpt.get("optimizer_state_dict"): optimizer.load_state_dict(ckpt["optimizer_state_dict"])
    if scheduler is not None and ckpt.get("scheduler_state_dict"): scheduler.load_state_dict(ckpt["scheduler_state_dict"])
    if ckpt.get("scaler_state_dict"): scaler.load_state_dict(ckpt["scaler_state_dict"])
    if ema is not None and ckpt.get("ema_state_dict"): ema.load_state_dict(ckpt["ema_state_dict"])
    return ckpt.get("best", float("inf")), ckpt.get("global_step", 0), ckpt.get("epoch", -1) + 1, ckpt.get("wandb_id")


def write_manifest(out_dir: Path, cfg: dict, device):
    """Reproducibility capture (versions, seed, git SHA, resolved config) so a run
    can be reconstructed later. Written automatically at startup."""
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        sha = None
    manifest = {
        "run_name": cfg["run"]["name"], "seed": cfg["run"]["seed"],
        "python": platform.python_version(), "torch": torch.__version__, "cuda": torch.version.cuda,
        "device": str(device), "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "git_sha": sha, "config": cfg,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))


def save_ckpt(path, *, epoch, global_step, best, raw_model, optimizer, scheduler, scaler, metrics, cfg, wandb_id, ema=None):
    """Write a fully resumable checkpoint (model + optimizer + scheduler + scaler +
    bookkeeping; + EMA if enabled). last.pt is written each epoch/cadence so a killed
    run resumes cleanly. model_state_dict is always the live (training) weights."""
    torch.save({
        "epoch": epoch, "global_step": global_step, "best": best,
        "model_state_dict": raw_model.state_dict(), "optimizer_state_dict": optimizer.state_dict(),
        "scheduler_state_dict": scheduler.state_dict() if scheduler else None,
        "scaler_state_dict": scaler.state_dict(), "wandb_id": wandb_id,
        "ema_state_dict": ema.state_dict() if ema is not None else None,
        "metrics": metrics, "config": cfg,
    }, path)


###############################################################################
################################# Evaluation ##################################
###############################################################################

@torch.inference_mode()
def evaluate(model, loader, criterion, device, amp, amp_dtype):
    """Score over a loader: mean loss, plus accuracy for integer-label classification
    (skipped for regression/seq tasks, where argmax-accuracy is meaningless)."""
    model.eval()
    total_loss, total_correct, total_n, classify = 0.0, 0, 0, False
    for batch in loader:
        X, y = to_device(batch, device)
        with autocast_ctx(device, amp, amp_dtype):
            logits = model(X)
            loss = criterion(logits, y)
        total_loss += loss.item() * len(y)
        # Accuracy only applies to 2-D logits with integer class labels.
        if logits.ndim == 2 and not torch.is_floating_point(y):
            classify = True
            total_correct += (logits.argmax(1) == y).sum().item()
        total_n += len(y)
    out = {"val_loss": total_loss / total_n}
    if classify:
        out["val_acc"] = total_correct / max(1, total_n)
    return out


###############################################################################
################################ Training loop ################################
###############################################################################

def train_once(cfg: dict, build_model=build_model, build_datasets=build_datasets,
               build_loss=build_loss, build_optimizer=build_optimizer) -> dict:
    """Run one full training from a resolved config dict; return result metrics.

    build_model / build_datasets / build_loss / build_optimizer default to the core
    implementations but an experiment can pass its own (see core/run.py) — that is the
    override seam (e.g. a custom build_optimizer for layer-wise LR decay). Device /
    precision / DDP are auto-resolved (utilities/hardware.py)."""

    # --------------------------------- Setup ---------------------------------

    # Seed, device, precision, DDP — all auto-resolved from the environment.
    set_seed(cfg["run"]["seed"])
    info = dev.ddp_info()
    device = dev.pick_device(cfg["run"].get("device", "auto"), info["local_rank"])
    dev.setup_distributed(info, device)
    main_proc = dev.is_main(info)
    amp, amp_dtype, use_scaler = dev.resolve_precision(device, cfg["train"]["amp"], cfg["train"].get("amp_dtype", "auto"))
    if device.type == "cuda":
        torch.backends.cudnn.benchmark = cfg["train"]["cudnn_benchmark"]

    # Run directory (results/<exp>/run_<ts>/, set by core/run.py) and its layout.
    out_dir = Path(cfg["run"].get("dir") or Path(cfg["run"]["out_dir"]) / cfg["run"]["name"])
    ckpt_dir = out_dir / "checkpoints"
    if main_proc:
        for d in (out_dir, ckpt_dir, out_dir / "logs", out_dir / "figures"):
            d.mkdir(parents=True, exist_ok=True)
    log = tracking.setup_logging(out_dir / "logs", main_proc)
    t0 = time.time()

    # Data — the train set is sharded across ranks under DDP.
    train_ds, val_ds = build_datasets(cfg)
    train_loader, val_loader, train_sampler = build_loaders(cfg, train_ds, val_ds, ddp=info)

    # Model on device BEFORE the optimizer; keep raw_model for opt/clip/checkpoint.
    model, raw_model = wrap_model(build_model(cfg), info, device, cfg["train"].get("compile", False))

    # Loss, optimizer (built on raw params), scheduler, AMP scaler.
    criterion = build_loss(cfg)
    optimizer = build_optimizer(cfg, raw_model)   # raw params == DDP params (same tensors)
    scheduler, sched_step = build_scheduler(cfg, optimizer, steps_per_epoch=loader_len(train_loader))
    scaler = torch.amp.GradScaler(device.type, enabled=use_scaler)

    # Optional weight EMA: eval + checkpoints use the smoothed weights, training the live
    # ones. Common for diffusion/GAN/SSL and modern vision (set train.ema_decay, e.g. 0.9999).
    ema = None
    if cfg["train"].get("ema_decay", 0):
        from torch.optim.swa_utils import AveragedModel, get_ema_multi_avg_fn
        ema = AveragedModel(raw_model, multi_avg_fn=get_ema_multi_avg_fn(cfg["train"]["ema_decay"]))
    eval_model = ema.module if ema is not None else raw_model   # what eval / best-selection scores

    # Auto-resume from checkpoints/last.pt if this run dir has one (--resume target).
    best, global_step, start_epoch, wandb_id = float("inf"), 0, 0, None
    last_path = ckpt_dir / "last.pt"
    resumed = cfg["train"].get("resume", True) and last_path.exists()
    if resumed:
        best, global_step, start_epoch, wandb_id = resume_from_checkpoint(last_path, device, raw_model, optimizer, scheduler, scaler, ema)
        log.info(f"[resume] from {last_path} at epoch {start_epoch} (best={best:.4f})")

    # Manifest + metrics tracker (jsonl always, wandb if logging.wandb is on).
    if main_proc:
        write_manifest(out_dir, cfg, device)
    tracker = tracking.Tracker(out_dir, cfg, main_proc, resume_id=wandb_id)

    # Correctness gate (main only; skipped on resume — already proven once).
    if main_proc and not resumed and cfg["train"].get("sanity_gate", True):
        sanity.run_gate(raw_model, criterion, train_loader, build_opt=lambda m: build_optimizer(cfg, m),
                        device=device, num_classes=cfg["model"].get("num_classes") or cfg["model"].get("out_features"),
                        overfit_steps=cfg["train"].get("sanity_overfit_steps", 300))
    dev.barrier(info)

    # Loop knobs pulled out once. save_best direction: "min" for losses, "max" for acc/AUC.
    accum = cfg["train"]["grad_accum_steps"]
    clip = cfg["optim"]["grad_clip_norm"]
    max_steps = cfg["train"].get("max_steps")
    ckpt_every = cfg["train"].get("ckpt_every", 0)
    eval_every_steps = cfg["train"].get("eval_every_steps", 0)   # 0 = epoch-based
    ckpt_every_steps = cfg["train"].get("ckpt_every_steps", 0)   # 0 = epoch-based
    save_max = cfg["train"].get("save_best_mode", "min") == "max"
    better = (lambda a, b: a > b) if save_max else (lambda a, b: a < b)
    if save_max and best == float("inf"):
        best = float("-inf")
    metrics = {}

    # Nested helper: write best.pt (on improvement) + last.pt from a metrics dict.
    def _checkpoint(epoch, m):
        nonlocal best
        ck = dict(epoch=epoch, global_step=global_step, raw_model=raw_model, optimizer=optimizer,
                  scheduler=scheduler, scaler=scaler, metrics=m, cfg=cfg, wandb_id=tracker.wandb_id, ema=ema)
        watch = m.get(cfg["train"]["save_best_on"])
        if watch is None:
            save_ckpt(ckpt_dir / "best.pt", best=best, **ck)   # no selection metric here — keep best.pt = latest
        elif better(watch, best):
            best = watch
            save_ckpt(ckpt_dir / "best.pt", best=best, **ck)
        save_ckpt(ckpt_dir / "last.pt", best=best, **ck)
        return ck

    # ----------------------------- Training loop -----------------------------

    for epoch in range(start_epoch, cfg["train"]["epochs"]):

        # Epoch setup: train mode, reshuffle DDP shards, fresh progress bar.
        model.train()
        if train_sampler is not None:
            train_sampler.set_epoch(epoch)        # reshuffle shards each epoch
        running = 0.0
        optimizer.zero_grad(set_to_none=True)
        i = -1
        n_batches = loader_len(train_loader)   # None for streaming/IterableDataset
        bar = tracking.progress(train_loader, main_proc, desc=f"epoch {epoch}", total=n_batches)

        # ── training loop ──
        for i, batch in enumerate(bar):

            # Forward + scaled backward (loss divided for gradient accumulation).
            X, y = to_device(batch, device)
            with autocast_ctx(device, amp, amp_dtype):
                logits = model(X)
                loss = criterion(logits, y) / accum
            scaler.scale(loss).backward()

            # Optimizer step every `accum` micro-batches: unscale, clip, step, sched.
            if (i + 1) % accum == 0:
                if clip is not None:
                    scaler.unscale_(optimizer)  # unscale before clipping
                    torch.nn.utils.clip_grad_norm_(raw_model.parameters(), clip)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
                if scheduler is not None and sched_step == "step":
                    scheduler.step()
                if ema is not None:
                    ema.update_parameters(raw_model)   # smooth the weights after each real step
                global_step += 1

            # Track the epoch's running loss; `stepped` = a real optimizer step.
            step_loss = loss.item() * accum
            running += step_loss
            stepped = (i + 1) % accum == 0

            # Per-step reporting (main process only, on real optimizer steps).
            if main_proc and stepped:
                lr = optimizer.param_groups[0]["lr"]

                # Live progress bar: current loss + LR.
                if hasattr(bar, "set_postfix"):
                    bar.set_postfix(loss=f"{step_loss:.4f}", lr=f"{lr:.2e}")

                # Periodic train-metric logging (every log_every steps).
                if global_step % cfg["train"]["log_every"] == 0:
                    tracker.log({"split": "train", "epoch": epoch, "step": global_step,
                                 "loss": step_loss, "lr": lr}, step=global_step)

                # Step-cadence eval + checkpoint (streaming/LLM, no epoch boundary).
                if eval_every_steps and global_step % eval_every_steps == 0:
                    m = {"train_loss": step_loss}
                    if val_loader is not None:
                        m.update(evaluate(eval_model, val_loader, criterion, device, amp, amp_dtype))
                        model.train()
                    log.info(f"step {global_step:6d}  " + "  ".join(f"{k} {v:.4f}" for k, v in m.items()))
                    tracker.log({"split": "eval", "epoch": epoch, "step": global_step, **m}, step=global_step)
                    _checkpoint(epoch, m)
                
                # Step-cadence checkpoint only (no eval).
                elif ckpt_every_steps and global_step % ckpt_every_steps == 0:
                    _checkpoint(epoch, {"train_loss": step_loss})

            # Stop mid-epoch once the global step budget is hit (all ranks).
            if max_steps and global_step >= max_steps:
                break

        train_loss = running / max(1, (i + 1))

        # Validation (main process, full val set) + per-epoch scheduler step.
        metrics = {"train_loss": train_loss}
        if main_proc and val_loader is not None and (epoch + 1) % cfg["train"]["eval_every"] == 0:
            metrics.update(evaluate(eval_model, val_loader, criterion, device, amp, amp_dtype))
        if scheduler is not None and sched_step == "epoch":
            # plateau keys off local train_loss on non-main DDP ranks — prefer a
            # per-step or cosine schedule for multi-GPU runs.
            if cfg["scheduler"]["name"] == "plateau":
                scheduler.step(metrics.get("val_loss", train_loss))
            else:
                scheduler.step()

        # Epoch-end logging + checkpoint (best/last, plus periodic snapshot).
        if main_proc:
            log.info(f"epoch {epoch:3d}  " + "  ".join(f"{k} {v:.4f}" for k, v in metrics.items()))
            tracker.log({"split": "epoch", "epoch": epoch, "step": global_step, **metrics}, step=global_step)
            ckpt_args = _checkpoint(epoch, metrics)            # best + last
            if ckpt_every and (epoch + 1) % ckpt_every == 0:   # periodic snapshot
                save_ckpt(ckpt_dir / f"epoch{epoch:04d}.pt", best=best, **ckpt_args)

        if max_steps and global_step >= max_steps:
            break

    # ------------------------------- Finalize --------------------------------

    if main_proc:
        wall = time.time() - t0
        log.info(f"done. best {cfg['train']['save_best_on']}={best:.4f}  ({wall:.0f}s)  -> {ckpt_dir/'best.pt'}")
        tracker.summary({"best": best, "save_best_on": cfg["train"]["save_best_on"],
                         "final": metrics, "wall_clock_s": round(wall, 1), "run_dir": str(out_dir)})
        tracker.finish()
    dev.cleanup(info)
    return {"best": best, "save_best_on": cfg["train"]["save_best_on"], **metrics}

# Entry point is core/run.py (composes an experiment's config + overrides with this
# loop). This module is import-only: `from core.train import train_once`.
