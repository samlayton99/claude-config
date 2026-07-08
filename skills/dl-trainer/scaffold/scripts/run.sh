#!/usr/bin/env bash
# run.sh — local launch of one experiment. Single-GPU or DDP via torchrun.
#   ./scripts/run.sh experiments/001_baseline           # single GPU/CPU/MPS
#   NPROC=8 ./scripts/run.sh experiments/001_baseline   # 8-GPU DDP
# Each run writes results/<name>/run_<datetime>/ (checkpoints/, logs/train.log, metrics).
set -euo pipefail
cd "$(dirname "$0")/.."   # run from workspace root

EXP="${1:?usage: run.sh experiments/<name>}"
NPROC="${NPROC:-1}"

uv sync                   # ensure the env matches uv.lock

if [[ "$NPROC" -gt 1 ]]; then
  uv run torchrun --standalone --nproc_per_node="$NPROC" -m core.run "$EXP"
else
  uv run python -m core.run "$EXP"
fi
