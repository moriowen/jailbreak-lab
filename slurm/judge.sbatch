#!/bin/bash
# Score every gen_*.json with the HarmBench classifier. From ~/scratch/HW4:
#   sbatch slurm/judge.sbatch          # full
#   sbatch slurm/judge.sbatch --smoke
#SBATCH -J hw4-judge
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
gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1 | tr ' ' '-')
export BDS_MACHINE="pace-ice-$gpu"
echo "node $(hostname)  gpu $gpu  start $(date)"
python -u -m src.check_judge
python -u -m src.judge "$@"
echo "done $(date)"
