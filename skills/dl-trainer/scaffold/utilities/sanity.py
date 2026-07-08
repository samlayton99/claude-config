"""sanity.py — the correctness gate train.py runs before the real loop (one batch,
fails loud so a broken setup never burns a full run): loss-at-init ≈ ln(classes),
overfit-one-batch → ~0, gradient-flow. See references/glossary.md for what each
catches and how to read a failure.
"""
from __future__ import annotations

import copy
import math

import torch


###############################################################################
################################### Checks ####################################
###############################################################################

def _first_batch(loader, device):
    batch = next(iter(loader))
    return [t.to(device) for t in batch]


def check_loss_at_init(model, criterion, X, y, num_classes=None, tol=0.5):
    """Init loss should sit near ln(num_classes) for balanced CE — far off means a
    head/label/reduction bug. Always fails on nan/inf."""
    model.eval()
    with torch.no_grad():
        loss = criterion(model(X), y).item()

    # Compare against the expected ln(classes) baseline when we know the class count.
    msg = f"[sanity] init loss = {loss:.4f}"
    if num_classes:
        expected = math.log(num_classes)
        msg += f"  (expected ~ln({num_classes}) = {expected:.4f})"
        ok = abs(loss - expected) <= tol * expected
        print(msg + ("  ok" if ok else "  WARN: far from expected — check head/labels/reduction"))
    else:
        print(msg)
    if not math.isfinite(loss):
        raise RuntimeError("[sanity] init loss is nan/inf — broken forward or loss")
    return loss


def check_overfit_one_batch(model, criterion, build_opt, X, y, steps=300, target=5e-2, rel_drop=0.3):
    """A correct model+loss+optimizer collapses ONE batch's loss far below its init
    value; a broken one stays near init. Pass on EITHER an absolute floor (`target`,
    for plain CE→0) OR a large relative drop (`final <= init*rel_drop`) — the relative
    arm is what keeps the check valid for losses that don't bottom at zero: label-
    smoothed CE (floors ~0.4), MSE (scale-dependent), slow-overfitting LLMs. Stochastic
    objectives (diffusion) won't collapse one batch — disable the gate there
    (train.sanity_gate=false) and rely on grad-flow instead."""
    m = copy.deepcopy(model).train()
    opt = build_opt(m)

    # Hammer the single batch for `steps`, then check the loss actually collapsed.
    init = criterion(m(X), y).item()
    loss = None
    for _ in range(steps):
        opt.zero_grad(set_to_none=True)
        loss = criterion(m(X), y)
        loss.backward()
        opt.step()
    final = loss.item()
    print(f"[sanity] overfit-one-batch loss {init:.4f} -> {final:.5f} after {steps} steps")
    if final > target and final > init * rel_drop:
        raise RuntimeError(f"[sanity] one batch did not overfit: {init:.4f} -> {final:.4f} "
                           f"(need < {target} abs, or < {init * rel_drop:.4f} = {int(rel_drop * 100)}% of init). "
                           "Fix model/loss/LR before training.")
    return final


def check_gradient_flow(model, criterion, X, y):
    """Every trainable param must get a finite, non-zero grad. Catch detached
    (no grad), dead (all-zero), and unstable (nan/inf) paths."""
    model.train()
    model.zero_grad(set_to_none=True)
    criterion(model(X), y).backward()

    # Classify each param's gradient; collect anything that isn't healthy.
    problems = []
    for name, p in model.named_parameters():
        if not p.requires_grad:
            continue
        if p.grad is None:
            problems.append((name, "no-grad (detached from graph)"))
        elif not torch.isfinite(p.grad).all():
            problems.append((name, "nan/inf grad"))
        elif p.grad.abs().max() == 0:
            problems.append((name, "all-zero grad (dead path)"))
    if problems:
        for name, why in problems:
            print(f"[sanity] GRAD PROBLEM  {name}: {why}")
        raise RuntimeError(f"[sanity] {len(problems)} parameter(s) have bad gradients")
    print("[sanity] gradient flow ok — all params receive finite non-zero grads")


###############################################################################
#################################### Gate #####################################
###############################################################################

def run_gate(model, criterion, loader, build_opt, device, num_classes=None, overfit_steps=300):
    """Run all checks on one batch. Raises on failure. Returns a dict of results.
    overfit_steps: lower it for very large models (the overfit check deep-copies the
    model) — set train.sanity_overfit_steps, or train.sanity_gate=false to skip."""
    print("─" * 60 + "\n[sanity] running correctness gate on one batch")
    X, y = _first_batch(loader, device)
    init = check_loss_at_init(model, criterion, X, y, num_classes)
    final = check_overfit_one_batch(model, criterion, build_opt, X, y, steps=overfit_steps)
    check_gradient_flow(model, criterion, X, y)
    print("[sanity] PASSED — setup is sound\n" + "─" * 60)
    return {"init_loss": init, "overfit_loss": final}
