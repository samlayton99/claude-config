# Run log — retrospective (compounding loop)

Personal, hard-won results from real runs. Exempt from the community-adoption bar
(this is YOUR data, not a claim about the field). Append one entry per real run.
Recurring findings here can later justify adjusting a task's `config.yaml` default — with a
note pointing back to the entries that motivated it (see
`~/.claude/skills/dl-trainer/rules/update-guidance.md`).

Append newest at the top. Keep entries short; link the run's `manifest.json`.

## Template

```
### <YYYY-MM-DD> — <task> — <run name>
- task: <tasks/<task> or "none">
- resolved config: <key deltas from the task config; or link runs/<name>/manifest.json>
- hardware: <gpu count / type>
- result: <final metric, did it converge, wall-clock>
- worked: <what helped>
- didn't: <what failed, and the fix>
- action: <none | proposed config change | new Watch candidate for tasks/<task>>
```

<!-- entries below -->

### 2026-06-27 — pinn — high-frequency Poisson 1D (precision demo)
- task: tasks/pinn
- resolved config: DeepXDE 1.15, u=sin(k*pi*x) on [0,1], k=4, FNN [1,64,64,64,64,1] tanh, Adam 15k @1e-3 -> L-BFGS. Identical config run at float32 and float64.
- hardware: Apple Silicon — float32 on MPS (Mac GPU), float64 on CPU.
- result: float32/MPS L2 rel err 6.9e-3; float64/CPU 1.1e-6 (~6000x better), same net/config. fp32 wall 129s, fp64 203s.
- worked: clean, reproducible demonstration of the recipe's "float64 REQUIRED" note. k=4 is a good difficulty — fp64 nails it, fp32 visibly floors; not so high that spectral bias muddies the comparison.
- didn't: the smoking gun is L-BFGS itself — in float32 it terminated after ~110 iterations (line search can't progress below fp32 resolution); in float64 it ran ~thousands of iters and kept refining. Adam-only error was similar (~1e-2) both ways; the precision gap is entirely the L-BFGS stage.
- gotcha (Mac-specific): Apple MPS is float32-only, so the *precise* fp64 PINN cannot run on the Mac GPU at all — it must fall to CPU. DeepXDE 1.15 sets torch's default device to mps:0 on import, so forcing float64 requires an explicit torch.set_default_device("cpu"). The Mac GPU can only ever run the imprecise (fp32) leg.
- action: none (confirms existing pinn.md guidance; recorded for the MPS float32-only constraint + the L-BFGS-iteration-count signature).

### 2026-06-28 — rl_ppo + rl_double_dqn — PPO vs Double DQN on classic gym control
- task: tasks/rl_ppo, tasks/rl_double_dqn (new task added this session)
- resolved config: CleanRL ppo.py + dqn.py vendored into core/ (update-math faithful). Double-DQN = online-net argmax selects, target-net evaluates. CartPole/MountainCar/LunarLander-v3, CPU, seed 1.
- hardware: Apple Silicon (MPS available) — but ran on CPU; classic-control nets are 64-120 wide MLPs where MPS dispatch overhead loses to CPU. CPU ~14-16k env-steps/s.
- result: CartPole 200k steps — PPO 22->418 best mean return (15s), Double DQN 22->363 (13s). PPO learns faster/higher per sample, as expected on-policy vs off-policy here. Clean comparison plot from metrics.jsonl.
- worked: single (non-vector) env for DQN avoids all gymnasium-1.0 autoreset bookkeeping — no spurious terminal->reset transition in the replay buffer, no final_observation handling. Storing done=termination-only (truncation bootstraps) is correct out of the box.
- didn't / GOTCHA (the big one): CleanRL master targets gymnasium 0.29 and reads finished-episode stats from infos["final_info"] + the terminal state from infos["final_observation"]. Installed gymnasium was 1.3.0, where the vector API changed to NEXT_STEP autoreset and episode stats moved to infos["episode"] masked by infos["_episode"]; the old keys are simply absent, so the unported logging silently records ZERO returns (exactly the trap rl_ppo.md flags). Adapter lives in core/env.py (episode_returns / single_episode_return). Also: LunarLander is v3 in gymnasium>=1.0 (was v2); gymnasium[box2d] builds fine on Mac.
- action: added tasks/rl_double_dqn (CleanRL dqn.py + van Hasselt double-target; check_reference clean, 11 tasks). Both RL task .md files already warn to verify the infos API vs the INSTALLED gymnasium — this run is concrete confirmation; no config change.
