# Image classification (from scratch) — ConvNeXt / ResNet on ImageNet-scale
_last updated: 2026-06-25_

**Hyperparameters live in `config.yaml`** (merged by `scaffold.py --task image_classification`).
The augmentation + regularization recipe is what makes from-scratch training work.

## Gold standard
- **timm / huggingface/pytorch-image-models** (~37k★, v1.0.27 May 2026; Ross Wightman) — THE
  classification reference: backbones, pretrained weights, reference `train.py`, named recipes.
- **ConvNeXt** (FAIR, CVPR 2022) — default modern ConvNet backbone.
- **DeiT / AugReg** — canonical ViT-on-ImageNet-1k recipe. **ResNet strikes back (A1/A2/A3)** —
  modern training of a vanilla ResNet-50.

## Recipe
- **Arch:** ConvNeXt-T @224. **Optimizer:** AdamW, **wd 0.05**, LR **4e-3 × batch/4096**
  (linear scaling), 20-epoch warmup, cosine, **300 epochs**.
- **Augmentation:** RandAugment m9-mstd0.5, **Mixup 0.8, CutMix 1.0**, Random Erasing 0.25.
- **Regularization:** label smoothing 0.1, drop-path 0.1(T)/0.4(S)/0.5(B), LayerScale 1e-6,
  weight EMA ~0.9999.
- **Loss:** cross-entropy with label smoothing (BCE for the ResNet RSB recipe).
- **Traps:** from-scratch needs the *full* aug/reg stack + long schedule; short runs underfit.
  ResNet-50 RSB-A2 alt: LAMB, BCE loss, CutMix 1.0, LR 5e-3 / wd 0.02 / 300 ep / batch 2048.

## Evidence
- **Adoption:** timm ~37k★ (actively maintained) — the practitioner standard.
- **Sources:** timm GitHub ; arXiv 2201.03545 (ConvNeXt), 2012.12877 (DeiT), 2106.10270 (AugReg),
  2110.00476 (RSB).
- **Bootstrap:** `pip install timm` → `train.py --model convnext_tiny --opt adamw --lr 4e-3
  --weight-decay 0.05 -b 1024 --epochs 300 --aa rand-m9-mstd0.5 --mixup 0.8 --cutmix 1.0
  --reprob 0.25 --smoothing 0.1 --drop-path 0.1 --model-ema`.
- _2026-06-25 — initial import from curated index._
