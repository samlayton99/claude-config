"""dataloader.py — the default Dataset + DataLoader. For your task, override build_datasets
in that experiment's experiment.py (store raw files under data/raw/; stream large data from
disk in __getitem__); the synthetic placeholder here is only so the scaffold runs its sanity
gate out of the box. build_loaders is shared plumbing. DataLoader knobs: references/glossary.md.
"""
from __future__ import annotations

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset, DistributedSampler, IterableDataset


###############################################################################
################################### Dataset ###################################
###############################################################################

class TaskDataset(Dataset):
    """Minimal Dataset (__len__ + __getitem__). For large data, store paths here and
    read each sample from disk in __getitem__ so workers stream in parallel."""

    def __init__(self, X: torch.Tensor, y: torch.Tensor):
        self.X = X
        self.y = y

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, i: int):
        return self.X[i], self.y[i]


def build_datasets(cfg):
    """Build the train/val Datasets. Replace the synthetic data with yours (keyed on
    cfg["data"]["train_path"] etc.). The placeholder is deliberately learnable so the
    scaffold passes its own sanity gate out of the box."""
    n, f, c = 2000, cfg["model"]["in_features"], cfg["model"]["out_features"]
    gen = torch.Generator().manual_seed(cfg["run"]["seed"])
    X = torch.randn(n, f, generator=gen)
    W = torch.randn(f, c, generator=gen)          # fixed projection → separable classes
    y = (X @ W).argmax(dim=1)
    split = int(0.9 * n)
    return TaskDataset(X[:split], y[:split]), TaskDataset(X[split:], y[split:])


###############################################################################
################################# DataLoaders #################################
###############################################################################

def _seed_worker(worker_id: int):
    # Each worker forks with its own RNG state — reseed NumPy per worker.
    np.random.seed(torch.initial_seed() % 2**32)


def build_loaders(cfg, train_ds: Dataset, val_ds: Dataset | None = None, ddp=None):
    """Build train (and optional val) DataLoaders from the `data:` config block.

    Returns (train_loader, val_loader, train_sampler). Under DDP (ddp["distributed"]),
    the train loader uses a DistributedSampler so each rank sees a disjoint shard;
    call train_sampler.set_epoch(epoch) each epoch. The val set is left whole (it is
    evaluated on the main process only). pin_memory is auto-disabled off-CUDA."""
    d = cfg["data"]
    g = torch.Generator(); g.manual_seed(cfg["run"]["seed"])

    # Knobs shared by both loaders (pin_memory is a no-op off CUDA).
    common = dict(batch_size=d["batch_size"], num_workers=d["num_workers"],
                  pin_memory=d["pin_memory"] and torch.cuda.is_available(),
                  persistent_workers=d["persistent_workers"] and d["num_workers"] > 0,
                  worker_init_fn=_seed_worker, generator=g)
    if d["num_workers"] > 0:
        common["prefetch_factor"] = d["prefetch_factor"]

    # Train loader: a DistributedSampler shards a map-style dataset under DDP. A
    # streaming IterableDataset can't be shuffled or sampled (it shards itself via
    # worker/rank info), so leave both off for it.
    is_iterable = isinstance(train_ds, IterableDataset)
    train_sampler = None
    if ddp is not None and ddp.get("distributed") and not is_iterable:
        train_sampler = DistributedSampler(train_ds, num_replicas=ddp["world_size"], rank=ddp["rank"], shuffle=True)
    train_loader = DataLoader(train_ds, shuffle=(train_sampler is None and not is_iterable),
                              sampler=train_sampler, drop_last=d["drop_last"], **common)

    # Val loader: no shuffle, keep every sample.
    val_loader = None
    if val_ds is not None:
        val_loader = DataLoader(val_ds, shuffle=False, drop_last=False, **common)
    return train_loader, val_loader, train_sampler
