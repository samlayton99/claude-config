# LLM finetuning (SFT / LoRA) — instruction-tune a pretrained LLM
_last updated: 2026-06-25_

**Hyperparameters live in `config.yaml`** (merged by `scaffold.py --task llm_finetune`).
For LoRA the few knobs below are the whole game — get them right.

## Gold standard
- **HuggingFace TRL** (~16k★) + **PEFT** (~19k★) — the standard SFT/LoRA stack.
- **"LoRA Without Regret"** (Thinking Machines, 2025) — the settled LoRA best-practice writeup.

## Recipe
- **`target_modules="all-linear"`** — the single most important finding; *not* attention-only.
- **Rank:** r=256 for SFT (r=1–32 for RL); `lora_alpha=16`, `lora_dropout=0.0`.
- **LR:** LoRA LR ≈ **10× full-FT LR** — SFT LoRA 2e-4 vs full-FT 2e-5. Cosine, grad clip 1.0.
- **Tricks & traps:** keep **effective batch < 32** (LoRA tolerates large batch worse than
  full-FT). Correctly configured LoRA matches full finetuning at ~⅓ less compute.
- **Loss:** next-token CE on the completion (mask the prompt).

## Evidence
- **Adoption:** TRL ~16k★, PEFT ~19k★ (HuggingFace) — the de-facto finetuning stack.
- **Sources:** huggingface.co/docs/trl/lora_without_regret ; thinkingmachines.ai/blog/lora.
- **Settled:** LoRA all-linear, LoRA-LR ≈ 10× full-FT, small effective batch.
- **Bootstrap:** `pip install trl peft` → `trl sft --use_peft --lora_r 256 --lora_alpha 16
  --lora_target_modules all-linear --learning_rate 2e-4 --packing`.
- _2026-06-25 — initial import from curated index._
