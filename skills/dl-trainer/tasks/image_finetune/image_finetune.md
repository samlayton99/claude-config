# Image finetuning — adapt a pretrained vision backbone
_last updated: 2026-06-25_

**Hyperparameters live in `config.yaml`** (merged by `scaffold.py --task image_finetune`).
Layer-wise LR decay is the knob that separates good finetuning from bad.

## Gold standard
- **timm** (~37k★) — pretrained backbones + the finetune recipe.
- **DINOv2** (~13k★, Apache-2.0) — download-and-use frozen SSL backbone (prefer over DINOv3
  per the conservatism rule unless you specifically need it).

## Recipe
- **Schedule:** ~**30 epochs**, AdamW LR ~**5e-5** (100× lower than scratch), short warmup.
- **Layer-wise LR decay ~0.8** — the key finetune knob (earlier layers learn slower).
- **Regularization:** lower/zero drop-path, keep label smoothing 0.1, EMA on; optionally
  finetune at 384 resolution.
- **Loss:** cross-entropy (with label smoothing).
- **Traps:** reusing scratch LRs torches pretrained features; skipping LLRD leaves accuracy on
  the table. For frozen-feature use, no finetuning needed — just read out DINOv2 embeddings.

## Evidence
- **Adoption:** timm ~37k★ ; DINOv2 ~13k★ (FAIR, Apache-2.0).
- **Sources:** timm GitHub ; dinov2 GitHub.
- **Bootstrap:** `timm.create_model('convnext_base.fb_in22k_ft_in1k', pretrained=True,
  num_classes=N)`, ~30 ep @ LR 5e-5 + LLRD 0.8. Frozen feats:
  `torch.hub.load('facebookresearch/dinov2','dinov2_vitl14')`.
- **Contested:** detection/seg framework choice — torchvision references = safest permissive
  default; Detectron2/MMDetection in maintenance mode; YOLO highest live adoption but AGPL-3.0.
- **Watch:** DINOv3 (newer, partial non-commercial license) — default to DINOv2.
- _2026-06-25 — initial import from curated index._
