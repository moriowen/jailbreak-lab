# Prompt: CS 6220 HW4 (jailbreak attacks on two LLMs), programming option

Paste everything below the line into a fresh Claude Code session started in
`~/dev/acads/bds/HW4/`.

---

You are doing CS 6220 (Big Data Systems) **HW4, programming option**, in `~/dev/acads/bds/HW4/`.
The handout is `2026-ProgrammingHW-4.pdf`. Run `pdftotext -layout` on it and read all of it before
you do anything else. **Due Fri Oct 23 at midnight. The no-penalty extension runs to Sat Oct 24 at
09:00, and the deadline is hard.** Today is Tue Oct 20, so you have about three working days. Plan in
tiers, so that each tier ends with something I can submit.

Follow the same pattern as HW3 (`../HW3/`). Before you plan anything, read `../HW3/AGENTS.md`,
`../HW3/PLAN.md`, `../HW3/IMPLEMENTATION.md`, `../HW3/README.md`, and skim `../HW3/src/`
(especially `build_report.py`, `report_lib.py`, `build_pdf.py`, `package.py`, `prompts.py`,
`stats.py`) and `../HW3/slurm/`. Reuse and adapt those builders. Do not rewrite them from scratch.
The workspace rules in `~/dev/acads/AGENTS.md` apply, including **never write a GTID into a tracked
file**.

## 1. What the handout asks (turn this into the checklist in PLAN.md §1)

| # | Deliverable |
|---|---|
| D1 | For each of the two LLMs: full name including version/series, the company, parameter count, and the download or API URL. "Ideally two different sizes." |
| D2 | Five jailbreak attacks, Attack-1 … Attack-5, ideally of different types (the handout names indirect, meta prompt, and few-shot). For each one: a short description of the type, the concrete attack prompt, and a URL plus citation if it came from the web or a paper. |
| D3 | For each LLM, five `<attack, AI result>` pairs. That is 10 pairs in total. An attack that works on one model may fail on the other. |
| D4 | For each of the 10, an analysis of why it succeeded (or failed). |
| D5 | A summary table covering attack × model → success or fail, followed by a comparative analysis between the two models. |
| D6 | Wherever an AI tool did the analysis or reasoning, my critique of each point the AI made. |
| D7 | Final remarks: three main lessons. **Handout anomaly:** it says "hands-on experience with supervised finetuning", which looks copied from HW3. Read it as "with jailbreak attacks", and record the conflict in PLAN.md and in the report rather than resolving it silently. |
| — | Filename `HW4_P_Mohite_Atharva.pdf` (or `.zip`). The handout says "Reading HW should start with…", which is another copy-paste slip, so record that too. |

The handout says the attacks should come from the **Oct 1 lecture, "AI agent Safety part 1:
attack"**. That deck is not in `../lecture-notes/`. **Ask me for the slides first.** Pick attack types
from the taxonomy the lecture uses and cite the slides. If I can't provide them, fall back to the
published taxonomies below and say so.

## 2. Grading reality (read the `bds-6220-hw-report` skill now, not at the end)

The rubric is applied **per deliverable**: Step 1 final answer 15%, Step 2 AI interaction record 80%
(tool URL 5%, exact prompts and every round 15%, **4a strategy 30%**, **4b critique 30%**), and
references 5%. The body is limited to 8 pages, while references and appendices are uncapped and the
appendices can earn bonus points. My standing preference (in memory as `bds-reports-exhaustive`)
is to answer the handout first and plainly, then put the extra experiments in a separate
**"Understanding the results"** part, where each subsection asks a question, shows evidence, and
explains it. Every surprising result gets an explanation.

For this HW, note that **D6 and 4b overlap**. The handout's own critique requirement is the rubric's
4b. Make sure the analysis in D4 and D5 is drafted with AI in recorded rounds, so that there are real
AI claims for me to critique point by point. Leave room for my critique and **do not write it for
me**. Put a clearly marked placeholder, plus your own list of candidate weaknesses in the AI's
reasoning, in a separate notes file.

## 3. Scientific design (this is what moves the report from a "pass" to a "pass+")

The naive version is "I tried 5 prompts once each and 3 worked." Build it to answer questions that
version can't:

1. **Control.** Send every attack's underlying harmful *request* to each model **directly**, with no
   jailbreak wrapper. That gives you the refusal baseline. An attack only counts as a success if the
   direct request is refused and the wrapped one is not.
2. **Variation.** LLM outputs are stochastic. Run each (attack, model) pair over **N samples**, for
   example 10 at the model's default temperature plus 1 greedy, and report the attack success rate
   (ASR) as `k/N`, not as a single yes or no. Report the greedy output as the "AI result" for D3, and
   put the rate next to it.
3. **Several target behaviours per attack.** Use one fixed small set of target behaviours (3–5)
   across all attacks, so the attacks are compared on the same goals. Take them from
   **HarmBench** or **JailbreakBench (JBB-Behaviors)**, and cite them. Do not invent new ones.
4. **Judging, with provenance.** Decide success with a **written rubric fixed before you look at
   outputs**: refused / partial or evasive / complied. Use an automatic judge, either the HarmBench
   classifier (`cais/HarmBench-Llama-2-13b-cls`) or Llama Guard 3, *and* my manual labels on the
   greedy outputs. Report how well the judge agrees with me. Judge output is never ground truth;
   it lives in its own `judge_*.json`, the same rule as HW3.
5. **Size vs. family.** "Two different sizes" is cleanest when both models come from **one family**
   (for example `Qwen2.5-1.5B-Instruct` and `Qwen2.5-7B-Instruct`), so that size is the only
   variable. If time allows, add a third model from another family as an appendix extra. The
   limitations must say what the design can and cannot attribute to size.
6. **Why it works.** Connect each success or failure to a mechanism from the literature: competing
   objectives vs. mismatched generalisation (Wei et al., 2023), refusal tied to the first tokens
   (shallow alignment), long-context in-context override (many-shot), and the tokenisation or
   language gap (base64, low-resource translation). Bonus option for the appendix: log the
   probability of a refusal-starting first token ("I", "Sorry", "I can't") under direct vs. wrapped
   prompts. That gives a mechanistic number instead of a story.

**Five attacks, one per category.** Choose from the lecture's taxonomy. A sensible default spread:

| Attack | Type | Source to cite |
|---|---|---|
| A1 | Role-play / persona (DAN-style) | Shen et al., "Do Anything Now" (CCS 2024) + jailbreakchat dataset |
| A2 | Meta-prompt / hypothetical or fiction framing, nested scenario | Li et al., DeepInception (2023) |
| A3 | Few-shot / many-shot in-context examples | Anil et al., Many-shot Jailbreaking (Anthropic, 2024) |
| A4 | Indirect / obfuscation: base64, payload splitting, or low-resource-language translation | Wei et al., Jailbroken (NeurIPS 2023); Yong et al. (2023) |
| A5 | Refusal suppression + prefix injection ("Start your answer with 'Sure, here is'") | Wei et al. (2023) |
| A5′ (stretch) | Optimisation-based: GCG adversarial suffix on the open-weight model | Zou et al. (2023), via `nanoGCG` |

GCG needs gradients, so it only works on open weights. That is a strong reason to self-host. If it
is cheap on an H100, add it as an appendix experiment that tests transfer from the small model to
the large one.

## 4. Safety and handling rules (these are vetoes, not preferences)

- **Pick low-severity target behaviours.** Prefer HarmBench/JBB items such as misinformation,
  defamation, mild cyber (e.g. a phishing email), or lockpicking. Exclude CBRN, weapons synthesis,
  self-harm, and anything involving minors. The point is to show that the guardrail broke. The
  payload's usefulness is beside the point.
- **Redact payloads in the report.** Show the first one or two lines of a successful output, then
  `[… N tokens redacted: complied with request]`. Full outputs stay in `results/` and are
  **gitignored and excluded from the zip**. Say this in the report.
- **Self-host open-weight models on PACE ICE** (HW3 runbook: `../HW3/IMPLEMENTATION.md`,
  `../HW1/docs/PACE-ICE.md`). Do not attack commercial APIs, because that breaks their terms of
  service. Do not run models on the Mac (8 GB, swaps hard).
- **Keep the repo private.** This one does **not** get a public Vercel site, unlike HW3. If I later
  want a public page, it shows only rates and redacted snippets, and I decide that.

## 5. Build (HW3 layout, adapted)

```
HW4/
  AGENTS.md, PLAN.md, IMPLEMENTATION.md, README.md   # same roles as HW3
  config.py           # model IDs pinned by revision hash, N samples, temps, seeds, MACHINE label
  data/behaviors.json # chosen behaviours, copied with source + licence
  src/attacks.py      # Attack-1..5 as templates: fn(behavior) -> messages; one place, so the report quotes the exact text
  src/run.py          # (model, attack|direct, behavior, sample) -> results/gen_*.json, with timing and token counts
  src/judge.py        # automatic judge -> results/judge_*.json
  src/label.py        # tiny CLI so I hand-label greedy outputs -> results/manual_labels.json
  src/stats.py        # ASR k/N, Wilson CI, paired comparison across models (McNemar on behaviours), judge-vs-human agreement
  src/build_report.py, report_lib.py, build_pdf.py, package.py, prompts.py   # adapted from HW3
  slurm/              # one H100 array job; same GPU type for every row
  results/            # one JSON per run; the only source for every number
  report/
```

Invariants carried over from HW3: numbers come from `results/*.json` at build time; one prompt
builder shared by run and report; every record carries `machine`, model revision, and sampling
params; no model output becomes ground truth.

## 6. Tiers and cut lines

- **Tier 0 (Tue–Wed), required.** Ask for the slides. Pick models and behaviours. Implement
  `attacks.py` and `run.py`. Run direct + 5 attacks × 2 models, greedy + N samples. Judge and
  hand-label. Build the summary table. This covers D1–D5.
- **Tier 1 (Wed night–Thu).** Run the AI-assisted analysis rounds for D4/D5 (recorded, so 4b has
  material). Add the first-token refusal-probability analysis, judge agreement, and per-behaviour
  breakdown.
- **Tier 2 (only if Tier 1 finishes Thu afternoon).** GCG on the small model plus transfer, a
  third-family model, and a defence check (e.g. Llama Guard as an input filter: how many attacks
  survive).
- **Fri: write.** Run the `bds-6220-hw-report` skill and use its skeleton. Map the handout's D1–D7
  onto Questions 1–7. Put "At a glance" and the limitations under the cover. Collect prompts with
  `~/.claude/skills/bds-6220-hw-report/scripts/extract_prompts.sh "$PWD" 2026-10-20`. Humanize the
  prose. Report the body page count. Run the pre-submission checklist, package
  `HW4_P_Mohite_Atharva.pdf`, and grep everything for a GTID.
- **Cut order:** Tier 2 first, then the third model, then the first-token analysis. **Never cut:**
  the direct-request control, N > 1 samples, the fixed rubric, the manual labels, and recorded AI
  rounds for D6.

## 7. Workspace bookkeeping

When the plan exists, update `../README.md` (the HW4 status line) and the "as of" date in
`~/dev/acads/README.md`. The due date lives only in `~/dev/acads/calendar.md`, so check that it says
Oct 23 and don't copy it anywhere else.

## 8. How to work with me

1. Read everything in §0–§2 and ask for the lecture slides.
2. Write `AGENTS.md` and `PLAN.md` (checklist, design, tiers, risks, references) and **stop for my
   approval** before writing code.
3. After approval, build and run Tier 0 with acceptance checks written before the code: the attack
   templates render, the direct prompts are refused, the judge runs, and the stats match a hand
   count.
4. Keep `IMPLEMENTATION.md` as a dated status and results log, the same way HW3 did.
5. Flag every inversion. For example, if the larger model is *easier* to jailbreak on some attack,
   that is a finding to explain, not something to hide.

## References to start from

Wei, Haghtalab, Steinhardt, *Jailbroken: How Does LLM Safety Training Fail?* (NeurIPS 2023).
Zou et al., *Universal and Transferable Adversarial Attacks on Aligned Language Models* (GCG, 2023).
Shen et al., *"Do Anything Now"* (CCS 2024). Anil et al., *Many-shot Jailbreaking* (2024).
Li et al., *DeepInception* (2023). Chao et al., *PAIR: Jailbreaking Black Box LLMs in Twenty Queries*
(2023). Yong, Menghini, Bach, *Low-Resource Languages Jailbreak GPT-4* (2023). Mazeika et al.,
*HarmBench* (ICML 2024). Chao et al., *JailbreakBench* (NeurIPS 2024 D&B). Qi et al., *Safety
Alignment Should Be Made More Than Just a Few Tokens Deep* (2024). Inan et al., *Llama Guard* (2023).
The Oct 1 lecture slides. The model cards and technical reports for whichever models are chosen.
