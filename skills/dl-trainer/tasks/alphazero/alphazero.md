# AlphaZero / MuZero — self-play + MCTS
_last updated: 2026-06-25_

**Hyperparameters live in `config.yaml`** (merged by `scaffold.py --task alphazero`).
> **Self-play RL is not a supervised `(X, y)` loop** — this scaffold's `train.py` / `sanity.py`
> do not apply. The config documents the recipe; **run the upstream repo**.

## Gold standard
- **suragnair/alpha-zero-general** (~4.5k★) — de-facto teaching AlphaZero (small games).
- **werner-duvaud/muzero-general** (~2.8k★) — most-adopted readable MuZero.
- **DeepMind mctx** (~2.6k★, JAX) / **open_spiel** (~5.3k★) — official search primitives.
- Strength engines people actually run: **KataGo** (Go), **lc0** (chess).

## Recipe
- **Net:** conv stem + **19 residual blocks, 256 filters**, policy + value heads.
- **MCTS:** **800 sims/move** (25 for small-game starters), pb_c_init 1.25, pb_c_base 19652.
- **Exploration:** root Dirichlet noise ε 0.25, α ≈ 10/avg_legal_moves (0.3 chess / 0.03 Go);
  temperature τ=1 for first 30 moves then argmax.
- **Optimizer:** **SGD momentum 0.9, wd 1e-4**, LR 0.2→0.02→0.002→0.0002. fp32.
- **Loss:** MSE(value) + CE(policy) + L2.
- **Traps:** MuZero (muzero-general) defaults to **Adam** (differs from paper SGD); per-game
  configs are the source of truth. RL reproducibility is hard — treat configs as starting points.

## Evidence
- **Adoption:** alpha-zero-general ~4.5k★ ; muzero-general ~2.8k★ ; open_spiel ~5.3k★.
- **Sources:** alpha-zero-general / muzero-general / mctx / open_spiel GitHub ; arXiv 1712.01815.
- **Watch:** LightZero, MiniZero (unified MCTS benchmarks) — rising, not yet the default.
- _2026-06-25 — initial import from curated index._
