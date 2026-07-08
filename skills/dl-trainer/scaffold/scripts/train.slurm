#!/usr/bin/env bash
# train.slurm — SLURM batch script for one experiment.
#   sbatch scripts/train.slurm experiments/001_baseline
# Edit partition/account/resources for your cluster before submitting.
#SBATCH --job-name=dl-train
#SBATCH --output=results/slurm/%x-%j.out
#SBATCH --error=results/slurm/%x-%j.err
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1                # request N GPUs: gpu:8
#SBATCH --cpus-per-task=8           # match DataLoader num_workers budget
#SBATCH --mem=64G
#SBATCH --time=24:00:00
##SBATCH --account=your_account     # uncomment + set if your cluster requires it

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-.}"                     # run from the workspace root

EXP="${1:?usage: sbatch scripts/train.slurm experiments/<name>}"
mkdir -p results/slurm                          # SBATCH --output dir must exist
module load cuda 2>/dev/null || true           # adjust to your cluster's modules

uv sync                                         # uv must be on PATH
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"

NGPU=$(echo "${SLURM_GPUS_ON_NODE:-1}")
if [[ "$NGPU" -gt 1 ]]; then
  srun uv run torchrun --standalone --nproc_per_node="$NGPU" -m core.run "$EXP"
else
  srun uv run python -m core.run "$EXP"
fi
