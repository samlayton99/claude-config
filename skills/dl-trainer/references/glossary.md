# Glossary & key tips — the training loop

Durable, hand-curated knowledge condensed from "The annotated PyTorch training
loop" (idlemachines.co.uk, 20 June 2026) plus standard practice. This file is
the tricks library: it encodes WHAT each operation does, WHEN each technique
applies, and HOW the loop silently breaks. The self-update process may extend
this file but must preserve the ordering rules and gotchas below verbatim.

The scaffold in `~/.claude/skills/dl-trainer/scaffold/` is the executable form of everything here.

---

## Where order matters (the silent-failure crib sheet)

None of these raise an exception. They corrupt the run quietly.

| Line | Wrong position | What breaks |
|---|---|---|
| `model.to(device)` | after `optimizer = ...` | with a dtype change (`.half()`), `.to()` allocates NEW Parameter objects; the optimizer holds the discarded originals and updates those. **Always build the optimizer after the model is on-device.** |
| `optimizer.zero_grad()` | after `loss.backward()` | gradients from batches accumulate; the step uses their sum, not this batch. |
| `clip_grad_norm_()` | before `loss.backward()` | `.grad` is empty → no-op. |
| `clip_grad_norm_()` | after `optimizer.step()` | clips gradients already applied → no effect. |
| `scheduler.step()` | inside the batch loop (epoch schedulers) | LR decays `len(loader)`× too fast per epoch. |
| omit `model.train()` after `eval()` | — | dropout off, BatchNorm frozen; trains in eval mode, no error. |
| omit `torch.no_grad()` in validation | — | autograd graph builds every val batch → memory grows → OOM. |
| log `loss` instead of `loss.item()` | — | pins the whole graph in memory. |

**The correct order inside the loop:** `zero_grad` → forward → loss → `backward` →
clip → `optimizer.step` → (`scheduler.step` if per-step). Per-epoch schedulers
step outside the batch loop.

---

## Data pipeline

- **Dataset** implements `__len__` and `__getitem__`. For data that doesn't fit
  in memory, load from disk inside `__getitem__` so workers stream in parallel.
- **DataLoader** knobs that matter:
  - `num_workers` 2–4 typical (depends on CPU/IO); 0 bottlenecks the GPU.
  - `pin_memory=True` enables async H2D copy — only helps with `num_workers>0` + CUDA.
  - `persistent_workers=True` avoids re-fork cost each epoch.
  - `drop_last=True` drops the ragged final batch (noisy BatchNorm on 2–3 samples).
  - `prefetch_factor=2` (default) — batches prefetched per worker.
- **Batch size:** powers of two / multiples of 8–16 align with tensor-core tiles.
  Smaller batch = noisier gradient = implicit regularization; larger = more memory.
- **`.to(device)` on a tensor is NOT in-place** (returns a new tensor); on an
  `nn.Module` it IS in-place for a device-only move.

## Reproducibility

- Seed CPU (`torch.manual_seed`), all GPUs (`cuda.manual_seed_all`), NumPy, and
  Python `random` — they are independent RNGs.
- `cudnn.deterministic=True` + `cudnn.benchmark=False` for exact reproducibility
  (slightly slower). They must be set together.
- With `num_workers>0`, each worker forks its own RNG — pass a `generator` and a
  `worker_init_fn` to make worker randomness reproducible.

## The model (`nn.Module`)

- `super().__init__()` is required (initializes the registry). Submodules/params
  assigned as attributes register automatically; plain attributes are excluded
  from `.parameters()`, `state_dict`, and `.to()`.
- `register_buffer` for tensors that follow the module but aren't trained
  (BatchNorm running stats, attention masks).
- Call `model(x)`, never `model.forward(x)` — `__call__` runs the hooks.
- `requires_grad=False` freezes a parameter (frozen layers, inference).
- `torch.compile(model)` (PyTorch 2.0+) fuses ops via Triton; first pass slow,
  then ~10–30% faster on GPU. `torch._dynamo.reset()` clears the cache.

## train() vs eval()

- `model.train()` / `model.eval()` only change **Dropout** (random mask vs
  identity) and **BatchNorm** (batch stats vs stored running stats). LayerNorm,
  GELU, ReLU are unaffected.
- Dropout uses *inverted* scaling at train time (×1/(1−p)) so inference needs no rescale.

## Gradients

- `zero_grad(set_to_none=True)` (default in 2.0+) is faster and frees memory;
  be careful if custom backward reads `.grad` directly.
- PyTorch **accumulates** gradients additively — this enables **gradient
  accumulation**: divide loss by `ACCUM_STEPS`, backward each micro-batch, step
  every `ACCUM_STEPS`. Effective batch = `batch_size × ACCUM_STEPS` (assumes
  mean-reduced loss). Standard when a full batch won't fit.
- **Backward** = reverse-mode autodiff; one pass gets all gradients for a scalar
  loss. Populates `.grad`; does NOT change weights.
- `retain_graph=True` — backward through the same graph more than once (GANs).
- `create_graph=True` — differentiate through backward (higher-order / meta).

## The graph & memory

- Forward builds a dynamic DAG; activations stay alive for backward → memory
  ~O(N·L). `torch.no_grad()` builds no graph (≈ halves memory, slightly faster).
- **Gradient checkpointing** (`torch.utils.checkpoint`) recomputes activations in
  backward instead of storing them — trades ~1 extra forward for much less memory.

## Loss (CrossEntropyLoss)

- = LogSoftmax + NLLLoss, fused for numerical stability (log-sum-exp trick).
  **Pass raw logits, not softmax outputs. Labels are integer indices, not one-hot.**
- `weight=` per-class tensor for imbalance; `label_smoothing=0.1` standard in
  modern vision/LM (prevents overconfidence); `ignore_index=-100` masks padding.
- `reduction='mean'` (default) divides by batch; switching to `'sum'` rescales
  the effective LR. **Log `loss.item()`, never the tensor.**

## Gradient clipping

- `clip_grad_norm_(params, max_norm)` rescales ALL grads by `max_norm/‖g‖` if the
  global L2 norm exceeds `max_norm` — preserves direction, bounds magnitude.
- `max_norm=1.0` is standard (GPT-2 and most LM/ViT work). Less needed for small
  MLPs on well-conditioned data. Transformers spike (attention saturation), so clip.
- `clip_grad_value_` clips per-element; does NOT preserve direction; rarely used.

## Optimizers

- **SGD+momentum:** `v=μv+g; θ-=ηv`. **Adam:** per-param first/second moment
  estimates with bias correction; robust to varying gradient scales.
  Defaults `β1=0.9, β2=0.999, ε=1e-8` (LM pretraining uses `β2=0.95`).
- **AdamW** decouples weight decay (`θ←(1-ηλ)θ - update`), not equivalent to Adam+L2;
  standard for transformers. **Do not weight-decay biases or norm params.**
- `fused=True` (CUDA) ~30–50% faster at scale; `foreach=True` intermediate, CPU-ok.
- Optimizer state is large: Adam on 7B params ≈ 56GB (m+v fp32) → 8-bit optimizers
  (bitsandbytes) or sharding (ZeRO) at scale.

## LR schedules

- Schedulers modify the optimizer's `lr` field. **Epoch schedulers step outside
  the batch loop; per-step schedulers (warmup) step every optimizer step.**
- **Cosine annealing** decays `η_max→η_min` over `T_max`. Modern standard =
  **linear warmup (1–5% of steps) + cosine decay**.
- `ReduceLROnPlateau` is the exception: call `scheduler.step(val_loss)`.

## Validation

- `model.eval()` and `torch.no_grad()` are **independent**; use both. eval changes
  layer behavior; no_grad stops graph construction.
- `torch.inference_mode()` is a stricter, ~10% faster no_grad (tensors can't
  re-enter autograd). Use for pure inference/validation.

## Checkpointing

- Save `model.state_dict()` **and** `optimizer.state_dict()` (+ scheduler, epoch).
  Resuming without optimizer state restarts Adam's moments cold → loss spike.
- `state_dict` has no class definition — the class must be importable to load.
- `map_location=device` handles cross-GPU loads. Save on best val loss, not last.
- torch.compile prefixes keys with `_orig_mod.` — strip it when loading into a
  non-compiled model.

## GPU efficiency (mostly free speed)

- **Device placement:** model + batch on the same GPU. Build the optimizer AFTER
  moving the model. `x.to(device, non_blocking=True)` overlaps transfer with
  compute — only with `pin_memory=True`.
- **Mixed precision:** tensor cores run fp16/bf16 matmuls 4–8× faster.
  - **bfloat16** — same exponent range as fp32, no underflow, **no GradScaler**.
    Preferred on A100/H100/TPU. This is the scaffold default.
  - **float16** — needs `GradScaler` (scale loss by ~2^16 before backward, unscale
    before clipping, skip step on inf/nan). Use the current `torch.amp` API.
- **cudnn.benchmark=True** picks the fastest conv algo per shape — only if input
  shapes are fixed (re-profiles on every new shape otherwise).
- **torch.compile** fuses elementwise ops; `mode='max-autotune'` for long runs.

## Sanity checks before a real run (proof, not assertion)

The scaffold's `utilities/sanity.py` runs checks 1–3 automatically before each run (1 is
reported and only checked for cross-entropy; 2 and 3 are enforced — a failure aborts the run).
Check 4 is a manual technique, not automated.

1. **Loss at init** ≈ `ln(num_classes)` for balanced CE (3 classes → 1.0986).
   Far off → head/label/reduction bug.
2. **Overfit one batch** — its loss must collapse far below its init value (toward ~0 for plain
   CE; a large relative drop for label-smoothed/MSE/LM losses). If it can't, fix this first.
3. **Gradient flow** — every trainable param gets a finite, non-zero `.grad`.
   None → detached; all-zero → dead path; nan/inf → instability.
4. **LR range test** (manual) — sweep LR orders of magnitude on one batch; the largest LR
   that still decreases loss smoothly bounds the peak LR.
