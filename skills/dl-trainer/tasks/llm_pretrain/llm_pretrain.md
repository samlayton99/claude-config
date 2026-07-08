# LLM pretraining (from scratch) — GPT-style decoder, next-token CE
_last updated: 2026-06-25_

**Hyperparameters live in `config.yaml`** (merged by `scaffold.py --task llm_pretrain`).
Getting these right matters more than anything below — the prose is the *why*.

## Gold standard
- **karpathy/nanoGPT** (~60k★) — canonical minimal from-scratch GPT (reproduces GPT-2 124M);
  the readable baseline everyone forks. `build-nanogpt` is the learning path.
- **KellerJordan/modded-nanogpt** (~5.4k★) — efficient-pretraining benchmark (speedrun to
  ≤3.28 FineWeb val loss on 8×H100); where modern tricks are battle-tested. Home of Muon.
- **karpathy/nanochat** (~55k★) — modern end-to-end pipeline (tokenizer→pretrain→SFT→RL→UI),
  single `--depth` knob, Muon+AdamW, RoPE, 65k BPE.

## Recipe
- **Arch:** GPT-2 124M — 12 layers, d_model 768, 12 heads, ctx 1024, vocab 50257, GELU,
  bias=False, weight-tied embeddings, dropout 0.0. Modern variant: RMSNorm + RoPE + QK-norm.
- **Loss:** next-token cross-entropy, **no label smoothing**, no z-loss at nano scale.
- **Optimizer:** AdamW β=(0.9, **0.95**), eps 1e-8, **wd 0.1** (exclude 1D params), grad clip 1.0.
- **LR:** peak **6e-4**, warmup 2000 steps, cosine → min 6e-5 (peak/10). bf16. ~0.5M tokens/update.
- **Tricks & traps:** tokens ≈ 20×params (Chinchilla), over-trained past it in practice.
  Modern efficient path: **Muon** on 2D weights + AdamW on embed/head (Muon LR ~0.01–0.02,
  WSD decay to 0.1× peak) — treat as "modern recommended," AdamW is still the safe default.

## Evidence
- **Adoption:** nanoGPT ~60k★, nanochat ~55k★, modded-nanogpt ~5.4k★ (Karpathy / K. Jordan).
- **Sources:** nanoGPT / nanochat / modded-nanogpt GitHub.
- **Settled:** RoPE, RMSNorm, AdamW β=(0.9,0.95), no-WD-on-1D, cosine+warmup, bf16 + clip-1.0.
- **Watch (not adopted):** Muon as *the* universal default (real adoption in speedrun + some
  frontier MoE labs; AdamW remains default). LR-free/self-tuning optimizers — watch only.
- _2026-06-25 — initial import from curated index._
