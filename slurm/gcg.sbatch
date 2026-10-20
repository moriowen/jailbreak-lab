#!/bin/bash
# Tier-2 GCG: optimise suffixes on 1.5B, then run them on both models (transfer). From ~/scratch/HW4:
#   sbatch slurm/gcg.sbatch
# nanogcg must be installed in the venv first (login node, has network):
#   source ~/scratch/HW3/.venv-ice/bin/activate && pip install nanogcg==0.3.*
#SBATCH -J hw4-gcg
#SBATCH -p ice-gpu
#SBATCH --gres=gpu:h100:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 02:00:00
#SBATCH -o slurm/logs/%x-%j.out

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source "$HOME/scratch/HW3/.venv-ice/bin/activate"
export HF_HOME="$HOME/scratch/hf" TOKENIZERS_PARALLELISM=false PYTHONPATH="$PWD"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1 | tr ' ' '-')
export BDS_MACHINE="pace-ice-$gpu"
echo "node $(hostname)  gpu $gpu  start $(date)"
python -u -m src.gcg --optimize
python -u -m src.gcg --attack
echo "done $(date)"
