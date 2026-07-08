# Audio classification / tagging — finetune AST
_last updated: 2026-06-25_

**Hyperparameters live in `config.yaml`** (merged by `scaffold.py --task audio_classification`).

## Gold standard
- **AST** (Audio Spectrogram Transformer, MIT CSAIL; ~490k downloads/mo) — the plug-in audio
  classifier/tagger.
- **PANNs / CNN14** — canonical cheap pretrained audio-embedding backbone.

## Recipe
- **Frontend:** 16 kHz, **128-mel Kaldi fbank** (htk_compat, 25 ms / 10 ms), 1024 frames;
  normalize `(fbank − mean) / (std·2)` per dataset.
- **Augmentation:** SpecAugment **freqm 48, timem 192**, **mixup 0.5**.
- **Start from** `MIT/ast-finetuned-audioset-10-10-0.4593`.
- **Loss:** **BCE** for multi-label, CE for single-label.
- **Traps:** per-dataset fbank normalization matters; match the frontend the checkpoint expects.

## Evidence
- **Adoption:** AST ~490k downloads/mo (MIT CSAIL).
- **Sources:** AST GitHub + arXiv 2104.01778.
- _2026-06-25 — initial import from curated index._
