"""model.py — the default model + the MODELS registry (selection by `model.name`, same idea
as the loss/optimizer factories in optimization.py).

For ONE experiment, define your architecture in that experiment's experiment.py — override
build_model, or register a class into MODELS. PROMOTE it here only once it's reused across
experiments (see AGENTS.md "Promotion"). The placeholder MLP is here so the scaffold runs its
sanity gate out of the box. nn.Module basics: glossary.
"""
from __future__ import annotations

import torch.nn as nn


class MLP(nn.Module):
    """Placeholder baseline. Swap in — or add alongside — your architecture."""

    def __init__(self, in_features: int, hidden: int, out_features: int):
        super().__init__()  # required: initialises the module registry
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, out_features),
        )

    def forward(self, x):
        return self.net(x)


# name -> builder. Promote reusable models here; an experiment may also register its own
# (`from core.model import MODELS; MODELS["myarch"] = MyArch`) or override build_model outright.
MODELS = {"mlp": MLP}


def build_model(cfg):
    """Build the model named by cfg["model"]["name"] from MODELS; the remaining `model:` keys
    are constructor args. Override this in experiment.py when you want full control."""
    m = dict(cfg["model"])
    name = m.pop("name", "mlp")
    if name not in MODELS:
        raise KeyError(f"unknown model '{name}' — register it in MODELS or override build_model "
                       f"in your experiment.py (known: {sorted(MODELS)})")
    return MODELS[name](**m)
