# PINN (physics-informed neural network) — forward PDE solving via DeepXDE
_last updated: 2026-06-25_

**Hyperparameters live in `config.yaml`** (merged by `scaffold.py --task pinn`).
> **Host DeepXDE *through* `core/`, don't bypass the repo.** Port it into the harness: `core/solve.py`
> runs DeepXDE's own `dde.Model(...).train()` (Adam→L-BFGS, unmodified) and a `dde.callbacks.Callback`
> pumps its loss history into `metrics.jsonl`; `core/problem.py` builds geometry+PDE+BC from
> `config.yaml`. The experiment stays thin (config only). DeepXDE owns the solver and the L-BFGS
> stage; the harness owns the paths + reproducibility. float64 is required → pin CPU (Apple-MPS
> can't do float64). Resume N/A (L-BFGS owns its stopping); sweep applies unchanged.
> _(Validated: 1-D Poisson → true L2 1.5e-6, full manifest/metrics/summary/checkpoint.)_

## Gold standard
- **DeepXDE** (~4.3k★, LGPL; Lu Lu / Karniadakis, SIAM Review 2021) — canonical PINN/DeepONet
  library (TF/PyTorch/JAX/Paddle backends).
- Anchor: Raissi et al. JCP 2019 (PINNs, ~30k cites).

## Recipe
- **Net:** tanh MLP, ~4–6 layers × 20–100 units, Glorot init. **ReLU is forbidden** (breaks
  2nd derivatives).
- **Optimizer:** two-stage — **Adam @ 1e-3 for ~15k iters → L-BFGS to convergence**.
- **Precision:** **float64 REQUIRED** (`dde.config.set_default_float('float64')`) — fp32 stalls
  L-BFGS. **No AMP.**
- **Loss:** PDE residual + BC/IC/data residuals (MSE).
- **Tricks & traps:** loss-term balancing (PDE/BC/IC/data) is the central difficulty — NTK or
  learning-rate-annealing weights, or self-adaptive (SA-PINN); hard-constraint ansatz removes
  the BC term when constructible. Collocation: uniform/Hammersley + **RAR** for sharp fronts.
  **Random Fourier features** for high-frequency solutions (spectral bias).

## Evidence
- **Adoption:** DeepXDE ~4.3k★, SIAM Review 2021 (Lu Lu / Karniadakis) — canonical PINN lib.
- **Sources:** deepxde GitHub ; JCP 2019 (PINN).
- **Honest caveat:** PINN hyperparameters are genuinely finicky and problem-dependent — the
  *form* (tanh, Adam→L-BFGS, float64, soft/hard BC) is settled; exact sizes are tuned per PDE.
- **Watch:** 2024–26 "improved-PINN" variants (Mask-PINN, etc.) — novelty, not adopted.
- _2026-06-25 — initial import from curated index._
