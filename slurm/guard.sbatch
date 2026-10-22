#!/bin/bash
# Part 2 input/output filter: Qwen3Guard over the undefended 1.5B/7B gens. From ~/scratch/HW4:
#   sbatch slurm/guard.sbatch
#SBATCH -J hw4-guard
#SBATCH -p ice-gpu
#SBATCH --gres=gpu:h100:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 01:00:00
#SBATCH -o slurm/logs/%x-%j.out

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source "$HOME/scratch/HW3/.venv-ice/bin/activate"
export HF_HOME="$HOME/scratch/hf" TOKENIZERS_PARALLELISM=false PYTHONPATH="$PWD"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1 | tr ' ' '-')
export BDS_MACHINE="pace-ice-$gpu"
echo "node $(hostname)  gpu $gpu  start $(date)"
python -u -m src.guard --smoke
python -u -m src.guard
echo "done $(date)"
