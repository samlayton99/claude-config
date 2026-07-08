# ASR (speech-to-text) — finetune Whisper / wav2vec2
_last updated: 2026-06-25_

**Hyperparameters live in `config.yaml`** (merged by `scaffold.py --task asr`).
Never train ASR from scratch — finetune a pretrained encoder/seq2seq model.

## Gold standard
- **OpenAI Whisper** (~104k★; large-v3 ~5.7M downloads/mo) — dominant ASR; the
  download-and-finetune default.
- **wav2vec2 / HuBERT** (FAIR) — self-supervised encoder lineage; wav2vec2 + CTC is the
  standard encoder-only path.
- **HF transformers ASR recipe / Audio Course** — de-facto practitioner finetune path.

## Recipe
- **Frontend** (auto via `WhisperFeatureExtractor`): 16 kHz mono, log-mel **80** (128 for
  large-v3), n_fft 400 (25 ms), hop 160 (10 ms), padded to 30 s.
- **Optimizer:** AdamW β=(0.9,0.999) eps 1e-8 wd 0.0, **LR 1e-5** (tiny 3.75e-5 / base 2.5e-5),
  **500 warmup**, linear decay. Batch 16, **max_steps 5000**, **fp16 + gradient_checkpointing**,
  grad clip 1.0.
- **Loss:** seq2seq cross-entropy (CTC for the wav2vec2 path, LR 1e-4–3e-4, freeze feature encoder).
- **Traps:** **padded label ids → -100**; strip leading BOS in the collator; not streaming
  (chunk long audio). SpecAugment (LibriSpeech LD): freq mF=2 F=27, time mT=2 T=100, warp 80.

## Evidence
- **Adoption:** Whisper ~104k★ (large-v3 ~5.7M downloads/mo) — dominant.
- **Sources:** Whisper GitHub + arXiv 2212.04356 ; wav2vec2 arXiv 2006.11477 ; HuBERT 2106.07447 ;
  huggingface.co/blog/fine-tune-whisper.
- **Unsettled:** 2026 toolkit "default" splits NeMo / ESPnet / SpeechBrain.
- **Watch:** TTS has **no** consensus default (fragmented by license) — do not treat any as gold.
- _2026-06-25 — initial import from curated index._
