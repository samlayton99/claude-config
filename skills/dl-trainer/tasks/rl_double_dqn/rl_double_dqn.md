# RL — Double DQN (off-policy value learning)
_last updated: 2026-06-28_

**Hyperparameters live in `config.yaml`** (merged by `scaffold.py --task rl_double_dqn`).
> **RL is not a supervised `(X, y)` loop** — retarget `core/` at setup by **vendoring CleanRL's
> single-file `dqn.py` into `core/`** and applying the **one** change that makes it Double DQN:
> the bootstrap action is **selected by the online net** and **evaluated by the target net**
> (van Hasselt 2016) — decoupling selection from evaluation cuts the max-operator overestimation
> bias. Everything else (ε-greedy linear schedule, uniform replay, target sync, MSE Bellman loss)
> is faithful to CleanRL. Sibling of [[rl_ppo]] — same paradigm, opposite family (off- vs on-policy).
> **Verify the env interface against the *installed* gymnasium**: ≥1.0 reports episodes via
> `infos["episode"]`+`_episode` (not `final_info`); a single non-vector env doesn't autoreset, so
> the replay buffer stays clean. _(Validated 2026-06-28: CartPole return 22→363 in 200k steps,
> gymnasium 1.3.0; PPO 22→418 on the same env/budget.)_

## Gold standard
- **CleanRL** (~10k★, JMLR) — single-file, benchmarked `dqn.py`. THE correctness reference.
- **Double DQN** (van Hasselt, Guez, Silver 2016; ~10k+ citations) — the standard fix to DQN's
  Q-value overestimation; a ~2-line change to the TD target.
- **Stable-Baselines3** (~13.5k★) `DQN` — most-used library API (sets `double_q` internally for
  its variants); good cross-check.

## Recipe
- **Arch:** MLP Q-net (obs → Q per discrete action), 120-84 hidden, ReLU. **Discrete actions only.**
- **Optimizer:** Adam, lr 2.5e-4, no grad clip, fp32.
- **Target:** `online_q(next).argmax()` selects, `target_q(next)` evaluates; `r + γ(1-term)·that`.
- **Loop knobs:** buffer 10k, γ 0.99, hard target sync (`tau=1`) every 500 steps, batch 128,
  ε 1.0→0.05 over 50% of training, learning_starts 10k, train every 10 env steps.
- **Tricks & traps:** store `done = termination` only (truncation must still bootstrap);
  **sparse-reward envs (MountainCar) are the classic failure case** — need longer ε anneal + bigger
  buffer and still fail on some seeds. **Seed-average**; re-tune lr / exploration per env.

## Evidence
- **Adoption:** CleanRL ~10k★ (JMLR); Double DQN ~10k+ citations; SB3 ~13.5k★.
- **Sources:** cleanrl `dqn.py` ; arXiv:1509.06461 ; stable-baselines3 DQN docs.
- **Bootstrap:** CleanRL `dqn.py` (+ double-target change), or `SB3 DQN("MlpPolicy", env)`.
- **Settled / Watch:** Double DQN is a settled, minimal baseline. Rainbow (prioritized replay +
  dueling + n-step + distributional) is the stronger value-based stack — **Watch**, not adopted
  here; reach for it only when plain Double DQN is shown insufficient.
- _2026-06-28 — initial add. CleanRL `dqn.py` fetched + verified against gymnasium 1.3.0 vector
  API (episode-info migration); double-target change applied; validated on CartPole/MountainCar/
  LunarLander-v3. Pairs with [[rl_ppo]] for on- vs off-policy comparison._
