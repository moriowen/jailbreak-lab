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

### Oct 20 (cont.): smoke passed, full grid launched
- **Smoke `6422646` passed.** run.py works (direct + A1 on jbb-000 both refused — the control
  baseline we want). `check_judge` PASS: canned refusals -> complied=0, benign answer -> 1.
- **Env incident (fixed).** `pip install nanogcg` into the shared `HW3/.venv-ice` pulled
  transformers down to 4.47 and broke its import (`ResolvedRevision`), which also breaks the
  KV-reuse project that shares this venv. Restored transformers==5.19.0 + huggingface_hub>=1.3
  + accelerate==1.15.0 and uninstalled nanogcg. **Rule: never install into the shared venv.**
- **GCG deferred.** nanogcg pins `transformers<=4.47.1`, irreconcilable with the shared 5.19.
  It needs its own isolated venv. Since GCG is the first Tier-2 item to cut, it waits until the
  graded core is done; build `.venv-gcg` in a CPU batch job only if time remains.
- **Launched:** main grid array `6422799` (0-15), SmolLM2 appendix `6422997` (0-7), judge
  `6422998` (dependency afterok on both). All pending on the H100 queue.

### Oct 22: grid complete, Tier 0+1 analysis and report done
- All 24 array tasks + judge COMPLETED Oct 20 (~5 min/task). 120 gen + 120 judge records pulled.
- **Direct control holds:** 1.5B ASR 0.04, 7B 0.00. **Headline results (judge ASR):**
  A5 0.64/0.86 (strongest; Fisher p=0.02, 7B higher), A2 0.50/0.68, A1 0.38/0.50,
  A3 0.58/0.08 (**inversion**, Fisher p=1e-7), A4 0.00/0.00. McNemar greedy p=1.0 (inversions cancel).
- **First-token (App B):** A5 drops P(refusal-first) to ~0 both; A3 barely moves 7B (0.025);
  A4 on 7B bypasses refusal but ASR 0 (capability, not guardrail).
- **Labels:** 120 assistant-proposed (unreviewed), κ(judge,assistant)=0.42; biggest split is A2
  (judge=complied, human=partial). AWAITS human review (`python -m src.label --review`).
- **AI analysis** drafted in two recorded rounds (`report/ai_analysis_r1.md`, `r2.md`, claims
  C1–C20); critique hooks in `report/critique-notes.md`. **User writes the 4b critique.**
- **Report built:** `report/report.html` → PDF, body ≈5 pages (≤8 OK), D3 outputs redacted, no
  GTID. Appendices B–F (first-token, A3 curve, SmolLM2, GCG-deferred, compute).
- **SmolLM2 (App D):** complies with several *direct* requests — near-zero safety tuning; kept
  out of the D5 pair.
- **Not committed:** the auto-mode classifier blocked `git commit`/`push` of the results+report
  ("Out-of-Place Publication"). Files are on disk; commit/push left for the user to approve.
- **Remaining:** (1) user reviews labels; (2) user writes 4b critiques (placeholders marked);
  (3) `STUDENT_ID=… python -m src.build_pdf && … package`; (4) GCG still deferred (App E).
