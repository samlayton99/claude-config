"""optimization.py — loss + optimizer + LR schedule (the `loss:`/`optim:`/`scheduler:`
config blocks). Small factories; keep the branch your task uses, delete the rest.
The why behind the inline guardrails is in references/glossary.md.
"""
from __future__ import annotations

import math

import torch
import torch.nn as nn
from torch.optim.lr_scheduler import CosineAnnealingLR, LambdaLR, ReduceLROnPlateau


###############################################################################
#################################### Loss #####################################
###############################################################################

def build_loss(cfg):
    """CrossEntropy expects raw logits + integer labels (not softmax / one-hot)."""
    l = cfg["loss"]
    name = l["name"]

    # Cross-entropy: optional class weights, label smoothing, padding ignore_index.
    if name == "cross_entropy":
        weight = l.get("class_weights")
        if weight is not None:
            weight = torch.tensor(weight, dtype=torch.float32)
        return nn.CrossEntropyLoss(weight=weight, label_smoothing=l.get("label_smoothing", 0.0),
                                   ignore_index=l.get("ignore_index", -100))

    # Other heads: binary, regression, sequence (CTC).
    if name == "bce_with_logits":
        return nn.BCEWithLogitsLoss()
    if name == "mse":
        return nn.MSELoss()
    if name == "ctc":
        return nn.CTCLoss(blank=0, zero_infinity=True)

    raise KeyError(f"unknown loss '{name}'")


###############################################################################
################################## Optimizer ##################################
###############################################################################

def param_groups(model, weight_decay: float):
    """Split params: decay the 2D+ weights, never decay biases / norm scales."""
    decay, no_decay = [], []
    for name, p in model.named_parameters():
        if not p.requires_grad:
            continue
        (no_decay if p.ndim < 2 or name.endswith(".bias") else decay).append(p)
    return [{"params": decay, "weight_decay": weight_decay},
            {"params": no_decay, "weight_decay": 0.0}]


def build_optimizer(cfg, model):
    o = cfg["optim"]
    groups = param_groups(model, o["weight_decay"])
    name = o["optimizer"]

    # Adam family (fused kernel on CUDA) or SGD+Nesterov.
    if name in ("adamw", "adam"):
        cls = torch.optim.AdamW if name == "adamw" else torch.optim.Adam
        return cls(groups, lr=o["lr"], betas=tuple(o["betas"]), eps=o["eps"], fused=torch.cuda.is_available())
    if name == "sgd":
        return torch.optim.SGD(groups, lr=o["lr"], momentum=o["momentum"], nesterov=True)

    raise KeyError(f"unknown optimizer '{name}'")


###############################################################################
################################# LR schedule #################################
###############################################################################

def build_scheduler(cfg, optimizer, steps_per_epoch: int | None):
    """Returns (scheduler, step_unit). step_unit 'step' => call every optimizer
    step (warmup); 'epoch' => call once per epoch. steps_per_epoch is None for a
    length-less streaming loader — then cosine_warmup needs train.max_steps."""
    s = cfg["scheduler"]
    name = s["name"]

    # Simple schedules: none, plateau (keys off val loss), plain cosine.
    if name == "none":
        return None, "epoch"
    if name == "plateau":
        return ReduceLROnPlateau(optimizer, mode="min", patience=10), "epoch"
    if name == "cosine":
        return CosineAnnealingLR(optimizer, T_max=cfg["train"]["epochs"], eta_min=s["min_lr"]), "epoch"

    # Linear warmup -> cosine decay (the modern default; steps per optimizer step).
    if name == "cosine_warmup":
        total = cfg["train"].get("max_steps") or (steps_per_epoch and cfg["train"]["epochs"] * steps_per_epoch)
        if not total:
            raise ValueError("cosine_warmup needs train.max_steps for a length-less (streaming) loader")
        warmup = s["warmup_steps"]
        min_ratio = s["min_lr"] / cfg["optim"]["lr"] if cfg["optim"]["lr"] else 0.0

        def lr_lambda(step):
            if step < warmup:
                return step / max(1, warmup)
            progress = (step - warmup) / max(1, total - warmup)
            cosine = 0.5 * (1.0 + math.cos(math.pi * min(progress, 1.0)))
            return min_ratio + (1.0 - min_ratio) * cosine

        return LambdaLR(optimizer, lr_lambda), "step"

    raise KeyError(f"unknown scheduler '{name}'")
