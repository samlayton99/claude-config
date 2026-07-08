"""experiment.py — OPTIONAL per-experiment overrides.

Define any of build_model / build_datasets / build_loss / build_optimizer here to override
the core default for THIS experiment only. Whatever you don't define falls back to core. If
you only change knobs, delete this file and keep just config.yaml.

Rule: keep custom code contained to this folder and IMPORT shared pieces from
core/ utilities/ data/ — never copy or edit them for one experiment. When a model/loss/
optimizer becomes reused, PROMOTE it into core/ (see AGENTS.md "Promotion") — config is
unchanged because selection is by name.

Example — a custom architecture for this experiment only:

    import torch.nn as nn
    def build_model(cfg):
        m = cfg["model"]
        return nn.Sequential(nn.Linear(m["in_features"], m["hidden"]), nn.GELU(),
                             nn.Linear(m["hidden"], m["out_features"]))

Example — register local model(s) so config picks one by `model.name` (sweep-friendly; to
promote later, move the class to core/model.py and add it to MODELS — config stays the same):

    import torch.nn as nn
    from core.model import MODELS
    class MyArch(nn.Module): ...
    MODELS["myarch"] = MyArch                 # then set model.name: myarch (or sweep over it)

Example — build on / import a shared core model instead of rewriting it:

    from core.model import MLP

Example — custom optimizer (e.g. layer-wise LR decay for finetuning):

    def build_optimizer(cfg, model): ...

Signatures (all take the resolved config dict; build_optimizer also takes the model):
    build_model(cfg) -> nn.Module
    build_datasets(cfg) -> (train_ds, val_ds | None)
    build_loss(cfg) -> callable(logits, target) | nn.Module
    build_optimizer(cfg, model) -> torch.optim.Optimizer
"""
