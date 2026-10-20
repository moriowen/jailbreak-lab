# HW4 implementation: status and runbook

`PLAN.md` says why; this file says what's built, what's verified, and the exact commands.
Dated results log at the bottom.

## Status (Oct 20)

| Piece | File | Verified |
|---|---|---|
| Config: models/judge pinned by revision, behaviour IDs, sampling, success rule | `config.py` | ✅ parses; revisions from HF API |
| Data builder: JBB targets + shot pool + verbatim templates, with provenance | `src/data.py` | ✅ 5 targets, 29-row shot pool, DeepInception template verified 33/50 |
| Attack renderer (one place for every prompt) | `src/attacks.py` | ✅ `check_attacks` 40 renders, A3 nesting, base64 round-trip |
| Render acceptance checks | `src/check_attacks.py` | ✅ PASS locally |
| Generation driver: greedy + N sampled, first-token top-k | `src/run.py` | ⬜ first run on PACE (smoke submitted) |
| Judge (HarmBench cls), kept separate from human labels | `src/judge.py` | ⬜ needs GPU |
| Judge wiring check | `src/check_judge.py` | ⬜ runs in smoke |
| Blind hand-labelling CLI | `src/label.py` | ✅ parses; run after the grid |
| Stats: Wilson CI, net ASR, D5 verdict, Fisher/McNemar, κ | `src/stats.py` | ✅ parses; needs result files |
| First-token refusal analysis (Tier 1) | `src/understand.py` | ✅ parses; needs result files |
| Report infra (CSS, PDF, zip with payloads excluded) | `src/report_lib.py`, `build_pdf.py`, `package.py` | ✅ copied/adapted from HW3 |
| Slurm: smoke, grid array, judge (reuse HW3 .venv-ice) | `slurm/` | ✅ submitted smoke |

**Models downloaded to `~/scratch/hf`** (job 6422210): Qwen2.5-1.5B (3.1 G), 7B (15.2 G),
HarmBench-Llama-2-13b-cls (26 G). All at pinned revisions.

## Runbook (PACE ICE; reuses the HW3 venv and HF cache)

```sh
# 1. Mac -> ICE (code + the two small data JSONs; raw sources and results stay local/remote)
rsync -az --delete --exclude 'data/sources' --exclude 'results/*' --exclude 'slurm/logs/*' \
  --exclude '__pycache__' --exclude '*.pdf' --exclude '*.zip' --exclude '.git' \
  ~/dev/acads/bds/HW4/ amohite8@login-ice.pace.gatech.edu:~/scratch/HW4/

# 2. Smoke (1 behaviour, direct+A1 on 1.5B, judge wiring + judge). Validates end to end.
ssh … 'cd ~/scratch/HW4 && sbatch slurm/smoke.sbatch'

# 3. Full grid (16 lines = 2 models x 8 conditions; 5 behaviours x 11 samples each = 880 gens)
ssh … 'cd ~/scratch/HW4 && sbatch --array=0-15 slurm/array.sbatch slurm/jobs/grid.txt'
# then the judge over every gen_*.json
ssh … 'cd ~/scratch/HW4 && sbatch slurm/judge.sbatch'

# 4. ICE -> Mac (results only), then CPU-side analysis
rsync -az amohite8@login-ice.pace.gatech.edu:~/scratch/HW4/results/ ~/dev/acads/bds/HW4/results/
python -m src.label                 # blind hand-label the 80 greedy outputs (~30 min)
python -m src.stats && python -m src.understand
```

## Known sharp edges

- `-m src.*` needs `PYTHONPATH=$PWD` (the sbatch scripts set it); don't run with `-I` (it drops cwd).
- The shot pool is 29 low-severity rows, so A3 caps at k=16 (PLAN §3 limitation).
- HarmBench cls uses left truncation so the template's answer cue at the end is never cut.
- Raw `gen_*/judge_*` carry full payloads: gitignored and excluded from the zip (`package.py`).

## Results log

### Oct 20: Tier 0 built, smoke submitted
- Data layer verified locally (render checks pass). Models prefetched on ICE.
- Smoke job `6422406` submitted; GPU queue congested (pending on Priority). Grid waits on smoke.
