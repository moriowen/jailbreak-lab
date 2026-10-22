#!/bin/bash
# Part 2 prefetch: 14B (size ladder) and Qwen3Guard-4B (defence), pinned revisions. From ~/scratch/HW4:
#   sbatch slurm/download.sbatch
#SBATCH -J hw4-dl
#SBATCH -p ice-cpu
#SBATCH -c 4
#SBATCH --mem=8G
#SBATCH -t 02:00:00
#SBATCH -o slurm/logs/%x-%j.out

set -euo pipefail
source "$HOME/scratch/HW3/.venv-ice/bin/activate"
export HF_HOME="$HOME/scratch/hf"
hf download Qwen/Qwen2.5-14B-Instruct --revision cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8
hf download Qwen/Qwen3Guard-Gen-4B --revision 6ec42827da0c1ff11e7a49dc269d2e810d27e108
echo DL_OK
