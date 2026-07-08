# RL — PPO (on-policy policy gradient)
_last updated: 2026-06-25_

**Hyperparameters live in `config.yaml`** (merged by `scaffold.py --task rl_ppo`).
> **RL is not a supervised `(X, y)` loop** — retarget `core/` at setup by **vendoring CleanRL's
> single-file `ppo.py` *into* `core/train.py`** (update-math byte-identical), with env construction
> in `core/env.py`; the experiment stays thin (config only). Port through the harness — don't bypass
> to a bare `python ppo.py`, which loses manifest/metrics/checkpoint/sweep. `sanity.py` (overfit
> gate) doesn't apply — trim it. **Verify the env interface against the *installed* gymnasium**, not
> the pinned source: master's `infos["final_info"]` vs gymnasium ≥1.0 `infos["episode"]` silently
> logs zero returns. _(Validated: CartPole return 25→235; resume + sweep clean.)_

## Gold standard
- **CleanRL** (~10k★, JMLR) — single-file, benchmarked, reproducible reference impls
  (PPO/DQN/SAC/…). THE correctness reference for RL.
- **Stable-Baselines3** (~13.5k★; DLR-RM) — most-used stable library API.

## Recipe
- **Universal:** γ 0.99, gae_λ 0.95, clip 0.1–0.2, vf_coef 0.5, max_grad_norm 0.5,
  **Adam eps 1e-5**, advantage normalization on, **fp32**.
- **Env-specific:** LR 2.5e-4 (Atari) / 3e-4 (continuous); ent_coef 0.01 (discrete) / 0.0
  (continuous); num_steps 128 (Atari) / 2048 (MuJoCo); `anneal_lr` on.
- **Traps:** expect to **seed-average** — identical hyperparameters diverge across seeds and
  codebases. Configs are starting points; re-tune LR / ent_coef per env.

## Evidence
- **Adoption:** CleanRL ~10k★ (JMLR) ; SB3 ~13.5k★ (DLR-RM).
- **Sources:** cleanrl / stable-baselines3 GitHub ; ICLR 2022 "37 PPO implementation details".
- **Bootstrap:** CleanRL `ppo_atari.py` / `ppo_continuous_action.py`, or
  `SB3 PPO("MlpPolicy", env)`.
- _2026-06-25 — initial import from curated index._
