"""Emit the command list for the Slurm array (PLAN §5 grid).

    python -m src.jobs > slurm/jobs/grid.txt

One line per (model, condition[, k]). direct + A1/A2/A4/A5 once each; A3 at each shot count.
Generation and judging are separate phases: the array runs these gen lines, then one judge
job sweeps every gen_*.json.
"""
from config import MODELS, SHOT_COUNTS
from src import attacks


def lines():
    out = []
    for m in MODELS:
        for cond, k in attacks.conditions_with_a3_shots(SHOT_COUNTS):
            tail = f" --k {k}" if k else ""
            out.append(f"python -u -m src.run --model {m} --cond {cond}{tail}")
    return out


if __name__ == "__main__":
    print("\n".join(lines()))
