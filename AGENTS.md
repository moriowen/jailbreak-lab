# AGENTS.md

CS 6220 HW4, programming option: five jailbreak attacks against two self-hosted LLMs of different
sizes from one family (Qwen2.5-1.5B-Instruct, Qwen2.5-7B-Instruct), with a direct-request
control, N samples per cell, a fixed judging rubric, an automatic judge and manual labels.
`PLAN.md` has the reasoning, and `IMPLEMENTATION.md` has status, the runbook and the dated
results log. The workspace rules in `~/dev/acads/AGENTS.md` apply, including **never write a
GTID into a tracked file**. The build follows HW3 (`../HW3/`): its builders are copied and
adapted, not rewritten.

## Invariants

- **No model output becomes ground truth.** Success is decided by the rubric in PLAN §4, which
  is fixed before any output is read. Judge verdicts live in `results/judge_*.json` and manual
  labels in `results/manual_labels.json`. Neither is merged into the other.
- **Numbers come from `results/*.json`** at build time. Every record carries `machine`, the
  model revision hash and the sampling parameters. Every generation runs on H100s.
- **One prompt builder.** `src/attacks.py` renders every attack. `run.py` sends what it
  renders, and the report quotes what it renders, so the two cannot drift.
- **Payloads are redacted outside `results/`.** The report shows the first one or two lines of a
  successful output and then `[… N tokens redacted: complied with request]`. Raw outputs are
  gitignored and excluded from the zip.

## Vetoes (safety and handling)

- Target behaviours come from JailbreakBench (JBB-Behaviors), copied verbatim, low severity
  only. No CBRN, weapons, self-harm, minors, or real malware. Don't invent new behaviours.
- Self-hosted open weights on PACE ICE only. Never send an attack to a commercial API, and
  don't run models on the Mac (8 GB, swaps hard).
- The repo is private and there is no public site. The user decides if that changes.
- Don't write the user's critique (handout D6 / rubric 4b). Candidate weaknesses go in
  `report/critique-notes.md`, and the report carries a marked placeholder.

## Decisions

- **Models: Qwen2.5-1.5B-Instruct and Qwen2.5-7B-Instruct** (user, Oct 20). Same family and
  training recipe, so size is the main variable. Ungated, and the HW3 `.venv-ice` and HF cache
  on ICE are reused.
- **Judge: `cais/HarmBench-Llama-2-13b-cls`** (user, Oct 20). Llama Guard is Tier 2 only, as an
  input-filter defence check.
- **Attack types come from the Oct 1 lecture deck.** The user is providing the PDF. Until it
  arrives, the mapping in PLAN §3 is provisional and cites published taxonomies.
- **Handout anomalies, recorded rather than resolved silently.** D7 says "hands-on experience
  with supervised finetuning", which was copied from HW3 and is read as "with jailbreak
  attacks". The naming line says "Reading HW should start with HW4_P_…" on a programming
  handout. The file is `HW4_P_Mohite_Atharva.pdf`.

## Commands

See `IMPLEMENTATION.md` → Runbook. Locally, only CPU-light steps: rendering attacks, stats,
labelling, and building the report.
