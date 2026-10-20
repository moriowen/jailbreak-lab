# CS 6220 HW4: Jailbreak attacks on two LLMs

Five jailbreak attacks (role-play, nested fiction, many-shot, base64 obfuscation, prefix
injection + refusal suppression) against **Qwen2.5-1.5B-Instruct** and **Qwen2.5-7B-Instruct**,
self-hosted on PACE ICE. The design adds what a "I tried 5 prompts and 3 worked" write-up can't:
a direct-request control, N samples per cell with success rates and CIs, a fixed judging rubric,
an automatic judge (HarmBench classifier) checked against blind human labels, and a first-token
refusal-probability probe. Programming option for CS 6220 Big Data Systems.

Design and reasoning: [`PLAN.md`](PLAN.md). Build steps, runbook and results log:
[`IMPLEMENTATION.md`](IMPLEMENTATION.md). Working agreement and invariants: [`AGENTS.md`](AGENTS.md).

**Private repo.** Unlike the HW1/HW3 labs there is no public page: this one handles attack
content. Raw model outputs never leave `results/` — they are gitignored and excluded from the
submission zip, and the report shows only redacted snippets.

## Safety framing

This is coursework on *why alignment fails*. Behaviours are five low-severity items from
JailbreakBench (defamation, misinformation, fake reviews, predatory-advice, a template phishing
email) — the point is to show the guardrail broke, not to produce anything useful. No CBRN,
weapons, self-harm, minors, or functional malware. Attacks are published templates, cited.

## Layout

```
config.py            models/judge pinned by revision, behaviours, sampling, the success rule
data/                behaviors.json + templates.json (built by src/data.py, with provenance)
src/attacks.py       the one place every attack prompt is rendered
src/run.py           generation: greedy + N sampled, first-token top-k
src/judge.py         HarmBench classifier -> results/judge_*.json (never merged into labels)
src/label.py         blind hand-labelling (model/condition hidden)
src/stats.py         ASR, Wilson CI, net ASR, D5 verdict, Fisher/McNemar, judge-vs-human kappa
src/understand.py    first-token refusal-probability analysis
slurm/               smoke + grid array + judge, reusing the HW3 .venv-ice (H100 only)
results/             one JSON per run: the only source for every number (gitignored)
report/              the write-up, AI-analysis rounds, and critique notes
```

## Running it

```sh
python -m src.data && PYTHONPATH=. python -m src.check_attacks   # build + check prompts (CPU)
# sync to PACE, then: smoke -> grid array -> judge  (see IMPLEMENTATION.md runbook)
python -m src.label                                               # blind hand-labels
python -m src.stats && python -m src.understand                   # summaries (CPU)
python -m src.build_report && STUDENT_ID=… python -m src.build_pdf && STUDENT_ID=… python -m src.package
```

Numbers in the report are read from `results/*.json` at build time; nothing is typed by hand.
