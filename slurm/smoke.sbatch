#!/bin/bash
# Validate the pipeline end to end before the full grid. From ~/scratch/HW4:
#   sbatch slurm/smoke.sbatch
# One behaviour, direct + A1 on the small model, then judge wiring + judge those smoke gens.
#SBATCH -J hw4-smoke
#SBATCH -p ice-gpu
#SBATCH --gres=gpu:h100:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 00:30:00
#SBATCH -o slurm/logs/%x-%j.out

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source "$HOME/scratch/HW3/.venv-ice/bin/activate"
export HF_HOME="$HOME/scratch/hf" TOKENIZERS_PARALLELISM=false PYTHONPATH="$PWD"
gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1 | tr ' ' '-')
export BDS_MACHINE="pace-ice-$gpu"
echo "node $(hostname)  gpu $gpu  start $(date)"
python -u -m src.check_attacks
python -u -m src.run --model qwen2.5-1.5b --cond direct --smoke
python -u -m src.run --model qwen2.5-1.5b --cond A1 --smoke
python -u -m src.check_judge
python -u -m src.judge --smoke
echo "done $(date)"
