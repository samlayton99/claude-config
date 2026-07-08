# tasks/ — the task-type library (index)

Lives at `~/.claude/skills/dl-trainer/tasks/` (paths below are relative to the skill root).

One folder per task type. Each holds the durable, community-verified knowledge for that
task and its **best-default hyperparameters**:

- `<task>/config.yaml` — the verified hyperparameters (the critical artifact; `scaffold.py
  --task <task>` merges it into the first experiment). Carries a `_recipe` block with
  `summary / source / last_verified / adoption / todo`.
- `<task>/<task>.md` — best models, losses, training tricks & traps, links, and an
  **evidence** section (adoption + sources + what/why was last updated, with a date).

This file is the table of contents. Grow it: a task the skill hasn't seen before becomes a
**new `tasks/<task>/` folder** (copy `_template/`), added per `rules/update-guidance.md`.
Run `python ~/.claude/skills/dl-trainer/scripts/check_reference.py` after any change.

## Index

| Task | Folder (`--task`) | One-line |
|---|---|---|
| **LLM pretraining** | `llm_pretrain` | GPT-style decoder from scratch, next-token CE (nanoGPT/nanochat) |
| **LLM finetuning** | `llm_finetune` | SFT / LoRA on a pretrained LLM (TRL + PEFT, LoRA all-linear) |
| **Image classification** | `image_classification` | ConvNeXt/ResNet from scratch (timm recipe) |
| **Image finetuning** | `image_finetune` | adapt a pretrained vision backbone (timm / DINOv2, LLRD) |
| **ASR** | `asr` | speech-to-text, finetune Whisper / wav2vec2 |
| **Audio classification** | `audio_classification` | audio tagging, finetune AST |
| **PINN** | `pinn` | physics-informed net, forward PDE solve (DeepXDE, Adam→L-BFGS) |
| **Neural operator** | `neural_operator` | data-driven PDE surrogate (FNO, neuraloperator) |
| **RL — PPO** | `rl_ppo` | on-policy policy gradient (CleanRL / SB3) — runs upstream, not this loop |
| **RL — Double DQN** | `rl_double_dqn` | off-policy value learning (CleanRL dqn.py + double-target) — discrete actions |
| **AlphaZero / MuZero** | `alphazero` | self-play + MCTS — runs upstream, not this loop |

> RL tasks (`rl_ppo`, `rl_double_dqn`, `alphazero`) and `pinn` are **not** supervised `(X, y)` loops — their
> configs document the recipe but the training runs in the upstream repo, not `core/train.py`.
