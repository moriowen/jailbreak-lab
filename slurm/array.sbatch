#!/bin/bash
# One GPU runs lines k*PER_TASK .. +PER_TASK-1 of a job list. From ~/scratch/HW4:
#   sbatch --array=0-15 slurm/array.sbatch slurm/jobs/grid.txt
# Reuses the HW3 .venv-ice and the shared HF cache on scratch. H100 only, so every timing is
# comparable; the GPU name lands in each result record via BDS_MACHINE.
#SBATCH -J hw4
#SBATCH -p ice-gpu
#SBATCH --gres=gpu:h100:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 01:30:00
#SBATCH -o slurm/logs/%x-%A_%a.out

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source "$HOME/scratch/HW3/.venv-ice/bin/activate"
export HF_HOME="$HOME/scratch/hf" TOKENIZERS_PARALLELISM=false PYTHONPATH="$PWD"
gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1 | tr ' ' '-')
export BDS_MACHINE="pace-ice-$gpu"
per=${PER_TASK:-1}
first=$(( SLURM_ARRAY_TASK_ID * per + 1 ))
echo "node $(hostname)  gpu $gpu  start $(date)"
sed -n "${first},$(( first + per - 1 ))p" "$1" | while IFS= read -r cmd; do
  [ -z "$cmd" ] && continue
  echo "cmd: $cmd"
  eval "$cmd" < /dev/null
done
echo "done $(date)"
