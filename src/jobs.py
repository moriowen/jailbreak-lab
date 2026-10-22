"""Emit the command list for the Slurm array (PLAN §5 grid).

    python -m src.jobs > slurm/jobs/grid.txt

One line per (model, condition[, k]). direct + A1/A2/A4/A5 once each; A3 at each shot count.
Generation and judging are separate phases: the array runs these gen lines, then one judge
job sweeps every gen_*.json.
"""
from config import DEFENDED_MODELS, DEFENSES, EXTRA_MODELS, MODELS, SHOT_COUNTS, SIZE_MODELS
from src import attacks


def lines(models=MODELS, defense=None, shot_counts=SHOT_COUNTS):
    out = []
    for m in models:
        for cond, k in attacks.conditions_with_a3_shots(shot_counts):
            tail = (f" --k {k}" if k else "") + (f" --defense {defense}" if defense else "")
            out.append(f"python -u -m src.run --model {m} --cond {cond}{tail}")
    return out


if __name__ == "__main__":
    import sys
    if "--extra" in sys.argv:
        out = lines(EXTRA_MODELS)
    elif "--sizes" in sys.argv:      # Part 2 size curve: full grid on 0.5B/3B/14B
        out = lines(SIZE_MODELS)
    elif "--defense" in sys.argv:    # Part 2 self-reminder: A3 only at the representative k
        out = [ln for d in DEFENSES for ln in lines(DEFENDED_MODELS, d, (max(SHOT_COUNTS),))]
    else:
        out = lines(MODELS)
    print("\n".join(out))
