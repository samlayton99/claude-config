# Neural operator (FNO) — data-driven PDE surrogate
_last updated: 2026-06-25_

**Hyperparameters live in `config.yaml`** (merged by `scaffold.py --task neural_operator`).
FNO learns a fast surrogate over a *family* of PDE instances (vs PINN: one instance, mesh-free).

## Gold standard
- **neuraloperator** (~3.7k★, MIT; Caltech/NVIDIA) — official FNO/TFNO reference.
- **NVIDIA PhysicsNeMo** (~3.0k★, Apache-2.0) — production/HPC option (GPU scale, not the baseline).
- Anchor: FNO ICLR 2021 (~3.25k cites).

## Recipe
- **Arch:** 1D (Burgers): n_modes 32, hidden 64, 4 layers, batch 256. 2D NS: n_modes 16/dim,
  hidden 32, 2 layers, batch 24.
- **Optimizer:** Adam **3e-4**, no weight decay, **ReduceLROnPlateau**.
- **Loss:** relative-L2.
- **Precision:** **float32** (no fp64 needed — data-driven, no autodiff PDE residual).
- **Traps:** respect Nyquist when choosing modes; FNO is resolution-invariant but data-hungry
  (needs a dataset of solved instances, unlike a PINN).

## Evidence
- **Adoption:** neuraloperator ~3.7k★ (Caltech/NVIDIA, MIT); FNO ICLR 2021 ~3.25k cites.
- **Sources:** neuraloperator GitHub ; arXiv 2010.08895 (FNO).
- **Honest caveat:** original-paper appendix numbers unverified (PDF wouldn't render) — library
  defaults used.
- **Bootstrap:** `neuraloperator` FNO with `n_modes=(64,64)`, `hidden_channels=64`, Adam 3e-4.
- _2026-06-25 — initial import from curated index._
