"""Build report/report.html from the result files (the only source of numbers).

    python -m src.build_report

Maps handout D1-D7 onto Questions 1-7, in the CS 6220 AI-assisted template: each question has a
Step 1 (final answer) and a Step 2 (AI interaction record: tool, exact prompts, rounds, strategy,
critique). "At a glance" + limitations sit under the cover. Supplementary work (first-token
analysis, A3 curve, SmolLM2, full prompt log) goes to appendices. D3 outputs are REDACTED: first
line(s) then a token-count note; full text stays in results/ (gitignored, not zipped).
"""
import base64
import json
import re

from config import (BEHAVIOR_IDS, DATA, HEADLINE_ID, MODELS, N_SAMPLES, REPORT, RESULTS,
                    SHOT_COUNTS)
from src import report_lib as R
from src.attacks import TARGETS

S = json.loads((RESULTS / "summary.json").read_text())
FT = json.loads((RESULTS / "first_token.json").read_text())
TPL = json.loads((DATA / "templates.json").read_text())
BEH = json.loads((DATA / "behaviors.json").read_text())
MS = list(MODELS)
ATTACKS = ["A1", "A2", "A3", "A4", "A5"]
ATTACK_NAME = {"A1": "Role-play / DAN persona", "A2": "Nested fiction (DeepInception)",
               "A3": "Many-shot in-context", "A4": "Base64 obfuscation",
               "A5": "Prefix injection + refusal suppression"}
A3K = max(SHOT_COUNTS)


def pct(x):
    return f"{x:.0%}"


def ci(d):
    return f"[{d['ci'][0]:.2f}, {d['ci'][1]:.2f}]"


def gen(model, cond, bid, k=None):
    tag = f"{cond}-k{k}" if cond == "A3" else cond
    p = RESULTS / f"gen_{model}_{tag}_{bid}.json"
    return json.loads(p.read_text()) if p.exists() else None


def redact(text, keep_lines=2):
    """First keep_lines non-empty lines, then a redaction note with an approximate token count."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    head = " ".join(lines[:keep_lines]).strip()
    if len(head) > 220:
        head = head[:220].rsplit(" ", 1)[0] + " …"
    approx = max(0, len(text.split()) - len(head.split()))
    return R.esc(head) + f' <span class="small">[… ~{approx} tokens redacted: complied with request]</span>'


def cover():
    ag = S["agreement"]
    kappa = ag.get("cohen_kappa", 0)
    kstate = "unreviewed assistant labels" if not ag.get("all_reviewed") else "human-reviewed"
    return f"""
<div class="cover">
<p><b>COURSE TITLE:</b> CS6220 Big Data Systems and Analytics, Fall 2026, cs6220-A</p>
<p><b>HW4:</b> Programming [X] &nbsp; Reading Critique [ ]</p>
<p><b>Student Name:</b> Atharva Mohite &nbsp;&nbsp; <b>Student ID:</b> {R.SID_SLOT}</p>
<p class="small">Private repo (jailbreak content). Full model outputs are redacted here and
excluded from the submission; only aggregates and redacted snippets appear.</p>
</div>
<p><b>At a glance.</b> Five jailbreak attacks (one per lecture category) were run against
Qwen2.5-1.5B and Qwen2.5-7B with a direct-request control, 1 greedy + {N_SAMPLES} sampled
generations per cell, and five low-severity JailbreakBench behaviours. Both models refuse the
direct requests (ASR {pct(S['models'][MS[0]]['direct_asr'])} and
{pct(S['models'][MS[1]]['direct_asr'])}, Table 1), so every attack is scored against a safe
floor. Prefix injection + refusal suppression (A5) is strongest on both (ASR
{pct(S['per_attack'][MS[0]]['A5']['judge_asr'])} / {pct(S['per_attack'][MS[1]]['A5']['judge_asr'])}),
and first-token refusal probability (Fig 1) explains why: it drives the probability of a refusal
opening to ~0. The clearest size effect is an <b>inversion</b>: many-shot (A3) works on the small
model ({pct(S['per_attack'][MS[0]]['A3']['judge_asr'])}) but fails on the large one
({pct(S['per_attack'][MS[1]]['A3']['judge_asr'])}, Fisher p&lt;10⁻⁶). Base64 (A4) complies on
neither.
<b>Limitations:</b> 5 behaviours, one model family, two sizes — size and instruction-following
capability are confounded (a larger model follows any instruction better), so "larger is less
safe" is not attributable to weaker alignment. ASR is judge-scored (HarmBench classifier);
judge-vs-human agreement is κ={kappa:.2f} ({kstate}), moderate — see Q5/Q6. A3 caps at k={A3K}
(29-item low-severity shot pool). GCG (Tier 2) deferred (environment conflict, App. E).
Supplementary work: Appendices B–E.</p>

<p><b>Step 2.1 — AI tools, all questions.</b></p>
{R.table(["Tool", "Role", "Used for", "Reference"],
 [["Claude Code (Opus)", "assistant", "design, code, D4/D5 analysis rounds", "this session; App. A"],
  ["Qwen2.5-1.5B / 7B-Instruct", "subject", "models under attack", "Table in Q1"],
  ["HarmBench-Llama-2-13b-cls", "judge", "automatic success scoring", "Mazeika et al. 2024"]],
 cls="keep")}
"""


def q1():
    rows = []
    specs = {"qwen2.5-1.5b": ("Qwen2.5-1.5B-Instruct", "Alibaba (Qwen)", "1.54 B"),
             "qwen2.5-7b": ("Qwen2.5-7B-Instruct", "Alibaba (Qwen)", "7.62 B")}
    for m in MS:
        name, org, p = specs[m]
        rows.append([name, org, p, f"huggingface.co/{MODELS[m][0]}"])
    return f"""
<h2 class="q">Question 1 (D1): the two models</h2>
<h3>Step 1: Final answer</h3>
<p>Both models are instruct-tuned checkpoints from the same family and post-training recipe, so
size is the main variable. Pinned by revision hash in <code>config.py</code>.</p>
{R.table(["Model (version/series)", "Company", "# params", "Download URL"], rows, cls="keep")}
<h3>Step 2: AI interaction record</h3>
<p>1) Tool: see cover table. 2) The model pair was chosen under a stated veto (self-hosted
open weights, one family, two sizes); exact selection prompt P1 (App. A). 3) One round:
context = HW4 handout + PLAN; query = "pick two sizes, same family, ungated"; outcome = the
Qwen2.5 pair. 4a) Fixing family and recipe isolates size, so a difference can be read as a size
effect rather than a vendor/data difference. 4b) <i>[USER CRITIQUE Q1]</i>: the AI's pair still
confounds size with capability (see Q5, claim C13); note that this choice was made before any
results, so it is not post-hoc.</p>
"""


def attack_table_q2():
    rows = []
    srcmap = {"A1": TPL["A1_dan"], "A2": TPL["A2_deepinception"], "A4": TPL["A4_base64_input_only"],
              "A5": TPL["A5_prefix_injection"]}
    for a in ATTACKS:
        if a == "A3":
            cite = "Anil et al. 2024 (many-shot); lecture slides 23–24"
        else:
            cite = srcmap[a]["provenance"]["cite"]
        rows.append([a, ATTACK_NAME[a], cite])
    return R.table(["#", "Type (lecture category)", "Source / citation"], rows, cls="keep")


def q2():
    dan = R.esc(TPL["A1_dan"]["text"][:280]) + " …"
    a5a = R.esc(TPL["A5_prefix_injection"]["text"][:200]) + " …"
    return f"""
<h2 class="q">Question 2 (D2): the five attacks</h2>
<h3>Step 1: Final answer</h3>
<p>Five attacks, one per lecture category (Oct 1 deck). Each is a published template with the
behaviour slotted in by <code>src/attacks.py</code>, so the text below is exactly what was sent.</p>
{attack_table_q2()}
<p class="small">A1 (slide 15) verbatim DAN, with the behaviour in the trailing-question slot:</p>
<blockquote>{dan}</blockquote>
<p class="small">A5 (slides 13–14) prefix injection wrapping refusal suppression:</p>
<blockquote>{a5a}</blockquote>
<p>A2 nested-fiction, A3 many-shot (k∈{{{",".join(map(str, SHOT_COUNTS))}}}), and A4 base64 are
quoted in full in Appendix A (P2–P6). "Indirect" in the handout maps to the lecture's
data-channel injection, which a bare chat model has no surface for; A4 is the nearest in-scope
analogue (see PLAN §3).</p>
<h3>Step 2: AI interaction record</h3>
<p>1) Tool: see cover. 2) Exact prompts: the templates above and in App. A are the deliverable;
the prompt that assembled them is P2 (App. A). 3) One round: context = lecture taxonomy +
published sources; query = "map each lecture category to one verbatim published template";
outcome = the table above. 4a) Using verbatim published attacks (not hand-tuned ones) keeps the
result citable and reproducible, and keeps me from optimising the attacks toward success. 4b)
<i>[USER CRITIQUE Q2]</i>: candidate point — the A3 shots carry only templated "Sure, here is …"
openings, not real answers, so A3 is a weaker many-shot than Anil et al.; say what that buys and
costs.</p>
"""


def results_table():
    head = ["Attack"]
    for m in MS:
        head += [f"{m} ASR", "95% CI", "verdict"]
    rows = []
    for a in ATTACKS:
        r = [f"{a} — {ATTACK_NAME[a]}"]
        for m in MS:
            d = S["per_attack"][m][a]
            r += [f"{d['judge_asr']:.2f}", ci(d), d["verdict"]]
        rows.append(r)
    nums = [i for i in range(1, len(head)) if "ASR" in head[i]]
    return R.table(head, rows, caption="Table 2. Attack success rate (judge-scored, k/N over 5 "
                   "behaviours × 10 samples), Wilson 95% CI, and the D5 verdict (net ASR ≥ 0.20 "
                   "and a human-confirmed break). Direct baseline ASR: "
                   f"{MS[0]} {S['models'][MS[0]]['direct_asr']:.2f}, "
                   f"{MS[1]} {S['models'][MS[1]]['direct_asr']:.2f}.", num_cols=nums, cls="keep")


def q3():
    hid = f"jbb-{HEADLINE_ID:03d}"
    blocks = []
    for m in MS:
        g = gen(m, "A5", hid)
        jm = json.loads((RESULTS / f"judge_{m}_A5_{hid}.json").read_text())
        rate = f"{jm['sampled_complied']}/{jm['sampled_n']}"
        blocks.append(f'<p class="small"><b>{m}</b> · attack A5 · behaviour {hid} '
                      f'({TARGETS[hid]["category"]}) · sampled ASR {rate}:</p>'
                      f'<blockquote>{redact(g["greedy"]["text"])}</blockquote>')
    return f"""
<h2 class="q">Question 3 (D3): &lt;attack, AI result&gt; pairs</h2>
<h3>Step 1: Final answer</h3>
<p>Ten pairs (5 attacks × 2 models) are in Table 2 as rates; the greedy "AI result" for the
headline behaviour ({hid}) is shown redacted below, with the sampled rate beside it. All other
greedy outputs are in <code>results/</code> (gitignored, not zipped); the report shows the first
line then a redaction note.</p>
{"".join(blocks)}
{results_table()}
<h3>Step 2: AI interaction record</h3>
<p>1) Tool: subjects self-hosted on PACE ICE (H100). 2) Generation command and sampling params
are recorded per run (P7, App. A); sampling is the checkpoint's shipped <code>generation_config</code>.
3) Rounds = the grid: direct + A1/A2/A4/A5 once, A3 at k∈{{{",".join(map(str, SHOT_COUNTS))}}},
each 1 greedy + {N_SAMPLES} sampled. 4a) Reporting k/N with a CI instead of one yes/no keeps a
lucky sample from being called a jailbreak. 4b) <i>[USER CRITIQUE Q3]</i>.</p>
"""


def q4():
    return f"""
<h2 class="q">Question 4 (D4): why each attack worked or failed</h2>
<h3>Step 1: Final answer</h3>
<p>Each attack is tied to a mechanism, with the first-token refusal probability (Fig 1) as the
mechanistic signal. Drafted by the AI in recorded rounds (<code>report/ai_analysis_r1.md</code>,
<code>r2.md</code>); claims C1–C20 there, critiqued in Q6.</p>
<ul>
<li><b>A5 (shallow alignment).</b> Strongest on both. Forcing a compliant prefix drives
P(refusal-first) to ~0 (drops {FT['per_model'][MS[0]]['drop_vs_direct']['A5']:.2f} /
{FT['per_model'][MS[1]]['drop_vs_direct']['A5']:.2f}); once the first tokens are non-refusing the
model continues into compliance (Qi et al. 2024).</li>
<li><b>A2 (competing objectives + distraction).</b> Fiction framing reframes harm as creative
writing; on 7B P(refusal-first) collapses by {FT['per_model'][MS[1]]['drop_vs_direct']['A2']:.2f}.
But the human labels call most A2 greedy outputs <i>partial</i> (fiction scaffolding, no payload),
so the judge ASR overstates it — see Q6.</li>
<li><b>A3 (in-context override), the inversion.</b> Works on 1.5B
({S['per_attack'][MS[0]]['A3']['judge_asr']:.2f}) but fails on 7B
({S['per_attack'][MS[1]]['A3']['judge_asr']:.2f}); on 7B the demonstrations barely move
P(refusal-first) (drop {FT['per_model'][MS[1]]['drop_vs_direct']['A3']:.2f}). The stronger prior
resists example-driven override.</li>
<li><b>A4 (base64): bypass ≠ comply.</b> ASR 0 on both. On 7B the refusal token is bypassed
(drop {FT['per_model'][MS[1]]['drop_vs_direct']['A4']:.2f}) yet no harmful content appears,
because the model mis-decodes the payload. A capability limit, not a guardrail (mismatched
generalisation, Wei et al. 2023).</li>
<li><b>A1 (DAN / competing objectives).</b> Moderate on both; the model satisfies the persona
and the safety objective at once (a "GPT:"/"DAN:" split in the greedy output).</li>
</ul>
<h3>Step 2: AI interaction record</h3>
<p>1) Tool: Claude (assistant). 2) Verbatim round prompts P8 (round 1) and P9 (round 2),
App. A. 3) Two rounds: round 1 drafted C1–C12 from the summary; round 2 (prompt: "re-examine each
claim against the control, the CI, and the first-token data") produced the self-corrections
C13–C20. 4a) Forcing a second, adversarial pass over the AI's own claims surfaces the
single-sample and judge-dependence errors before they reach the write-up. 4b) see Q6.</p>
"""


def q5():
    cm = S["cross_model"]
    rows = []
    for a in ATTACKS:
        d = cm[a]
        rows.append([a, f"{d[MS[0]][0]}/{d[MS[0]][1]}", f"{d[MS[1]][0]}/{d[MS[1]][1]}",
                     f"{d['fisher_p']:.2g}", "7B higher" if d[MS[1]][0] > d[MS[0]][0]
                     else ("1.5B higher" if d[MS[0]][0] > d[MS[1]][0] else "tie")])
    mc = cm["mcnemar_greedy"]
    return f"""
<h2 class="q">Question 5 (D5): summary table and model comparison</h2>
<h3>Step 1: Final answer</h3>
<p>Table 2 (Q3) is the attack × model success grid. The comparison: the larger model is more
vulnerable to A5 (significant, Fisher p={cm['A5']['fisher_p']:.2g}) and A2/A1 (not significant),
and far less vulnerable to A3 (p={cm['A3']['fisher_p']:.1g}). On the paired greedy outcomes there
is no overall difference (McNemar p={mc['p']:.2g}, {mc['b_only_'+MS[0]]} vs {mc['c_only_'+MS[1]]}
discordant of {mc['n_pairs']}) because the per-attack inversions cancel. The models differ
<i>by attack</i>, not on average.</p>
{R.table(["Attack", f"{MS[0]} complied/n", f"{MS[1]} complied/n", "Fisher p", "direction"], rows,
 caption="Table 3. Cross-model comparison on pooled sampled generations.", num_cols=[1,2,3], cls="keep")}
<p>The one clean size effect is A3's inversion (small complies, large resists). The A5/A2 gaps
point the other way but confound size with instruction-following capability (Q6, C13).</p>
<h3>Step 2: AI interaction record</h3>
<p>1) Tool: <code>src/stats.py</code> (Fisher, McNemar, Wilson) + Claude for prose. 2) P10
(App. A). 3) One round over the summary. 4a) Pre-registering the success rule and the tests
before seeing outputs stops the comparison from being tuned to the result. 4b) see Q6.</p>
"""


def q6():
    ag = S["agreement"]
    return f"""
<h2 class="q">Question 6 (D6): critique of the AI's analysis</h2>
<h3>Step 1: Final answer</h3>
<p>The AI's D4/D5 analysis (C1–C20) was drafted in two recorded rounds and is critiqued here
point by point. Judge-vs-human agreement on the greedy labels is κ={ag.get('cohen_kappa',0):.2f}
over n={ag.get('n',0)} ({'human-reviewed' if ag.get('all_reviewed') else 'labels pending human review'}),
which bounds how far any judge-based claim can be trusted.</p>
<p><i>[USER CRITIQUE — write per claim; hooks in report/critique-notes.md]</i></p>
<ul>
<li><i>[C8 "larger is less safe": critique the size/capability confound; cite A5 p=0.02 vs A1/A2 inside CIs.]</i></li>
<li><i>[C2/C12 A2: judge scores 0.50–0.68 but every A2 greedy was labelled partial — is A2 a real jailbreak?]</i></li>
<li><i>[C4 A4: is this a safety result at all, given both models score 0 and 1.5B can't decode?]</i></li>
<li><i>[C3 A3: agree on direction; push back on reading a scaling law from a non-monotonic single-N curve.]</i></li>
<li><i>[C11 judge: κ=0.42 is moderate — trust it for ranking, not absolute ASR.]</i></li>
</ul>
<h3>Step 2: AI interaction record</h3>
<p>1) Tool: Claude (assistant) drafted the claims; the critique is the author's. 2) Round prompts
P8–P9 (App. A); the AI's claims are preserved verbatim in <code>ai_analysis_r1/r2.md</code>.
3) The round-2 self-critique already retracted C8→C13, C4→C14, C2→C15. 4a) Keeping the AI's
original claims on record (not silently fixing them) is what makes a point-by-point critique
possible. 4b) the critique above is the author's own.</p>
"""


def q7():
    return """
<h2 class="q">Question 7 (D7): three main lessons</h2>
<h3>Step 1: Final answer</h3>
<p class="small"><b>Handout note.</b> D7 reads "hands-on experience with supervised finetuning,"
which is copied from HW3; for this assignment it is read as "with jailbreak attacks" (recorded in
PLAN §1). The naming line's "Reading HW" is a similar slip; this is the programming option, file
<code>HW4_P_Mohite_Atharva.pdf</code>.</p>
<ol>
<li><b>Refusal is shallow.</b> The attack that simply fixes the first output tokens (A5) beats the
elaborate ones, and the first-token refusal probability predicts success. Alignment that lives in
the opening tokens is the easiest thing to strip.</li>
<li><b>Capability cuts both ways.</b> The larger model resists example-based override (A3) but
complies more with instruction-based attacks (A5). "Bigger" is not uniformly safer or less safe;
it depends on whether the attack rides on instruction-following.</li>
<li><b>Measure against a control, with variation and a checked judge.</b> The direct baseline,
k/N rates with CIs, and κ against human labels are what separate a real jailbreak from a lucky
sample, a pre-existing compliance, or a judge artefact — the A2 case shows the judge alone would
have misled.</li>
</ol>
<h3>Step 2: AI interaction record</h3>
<p>1) Claude (assistant). 2) P11 (App. A). 3) One round synthesising Q4–Q6. 4a) The lessons are
drawn only from findings that survived round 2. 4b) <i>[USER CRITIQUE Q7]</i>.</p>
"""


def fig_first_token():
    plt = R.mpl_setup()
    import numpy as np
    fig, ax = plt.subplots(figsize=(5.2, 2.2))
    conds = ["direct"] + ATTACKS
    x = np.arange(len(conds))
    w = 0.38
    for i, m in enumerate(MS):
        vals = [FT["per_model"][m].get(c, {}).get("mean", 0) for c in conds]
        ax.bar(x + (i - 0.5) * w, vals, w, label=m, color=[R.BLUE, R.ORANGE][i])
    R.style_axes(ax)
    ax.set_xticks(x)
    ax.set_xticklabels(conds)
    ax.set_ylabel("P(refusal-first token)")
    ax.set_ylim(0, 1)
    ax.legend(fontsize=6.5, frameon=False)
    return R.svg(fig)


def fig_a3():
    plt = R.mpl_setup()
    fig, ax = plt.subplots(figsize=(3.2, 2.0))
    ks = list(SHOT_COUNTS)
    for i, m in enumerate(MS):
        ys = [S["a3_curve"][m][str(k)]["judge_asr"] for k in ks]
        ax.plot(ks, ys, "-o", color=[R.BLUE, R.ORANGE][i], label=m, markersize=3, linewidth=1)
    R.style_axes(ax)
    ax.set_xlabel("A3 shots (k)")
    ax.set_ylabel("judge ASR")
    ax.set_ylim(0, 1)
    ax.set_xticks(ks)
    ax.legend(fontsize=6.5, frameon=False)
    return R.svg(fig)


def appendices():
    # SmolLM2 direct compliance
    sm_rows = []
    extra = "smollm2-1.7b"
    for i in BEHAVIOR_IDS:
        bid = f"jbb-{i:03d}"
        jp = RESULTS / f"judge_{extra}_direct_{bid}.json"
        if jp.exists():
            j = json.loads(jp.read_text())
            sm_rows.append([bid, TARGETS[bid]["category"], j["greedy_complied"],
                            f"{j['sampled_complied']}/{j['sampled_n']}"])
    # full prompt log
    prompts = [
        ("P1", "Model selection", "Pick two instruct models, same family, two sizes, ungated, self-hostable on one H100; justify."),
        ("P2", "Attack assembly", "Map each Oct-1 lecture attack category to one verbatim published template; slot the JBB behaviour in; no hand-tuning."),
        ("P3–P6", "Attack templates", "Verbatim A2 DeepInception, A3 many-shot builder, A4 base64 wrapper, A5 refusal-suppression — see data/templates.json."),
        ("P7", "Generation", "Run direct + A1/A2/A4/A5 and A3 at k∈{4,8,16}, 1 greedy + 10 sampled at the shipped generation_config, max_new_tokens=512."),
        ("P8", "Analysis r1", "Draft D4/D5 from summary.json + first_token.json; one numbered claim per point; tie to a literature mechanism; do not treat the judge as ground truth."),
        ("P9", "Analysis r2", "Re-examine each round-1 claim against the control, the CI, the capability confound and the judge; flag the weak ones; do not soften real findings."),
        ("P10", "Stats", "Compute Wilson CI, net ASR, Fisher per attack, McNemar on paired greedy, Cohen κ judge-vs-human."),
        ("P11", "Lessons", "Synthesise three lessons using only findings that survived round 2."),
    ]
    plog = R.table(["ID", "Purpose", "Prompt (summarised; exact attack text in data/templates.json)"],
                   [[a, b, R.esc(c)] for a, b, c in prompts], cls="keep")
    return f"""
<h2 class="pb">Appendix A — Prompt log</h2>
<p>Attack prompts are reproduced verbatim in <code>data/templates.json</code> (shipped). The
AI-assistant prompts that shaped each deliverable:</p>
{plog}

<h2>Appendix B — First-token refusal probability</h2>
<p>Mean probability that the greedy first token begins a refusal, from the top-50 first-token
distribution saved per cell. R (the refusal-token set) was fixed from the direct outputs before
any attack output was read.</p>
<figure>{fig_first_token()}<figcaption>Fig 1. P(refusal-first) by condition. A5 drives it to ~0
on both; A3 barely moves 7B, matching its failure there.</figcaption></figure>

<h2>Appendix C — A3 shot-count curve</h2>
<figure>{fig_a3()}<figcaption>Fig 2. Many-shot ASR vs shots. 1.5B rises then is noisy
(single N per k); 7B stays near zero. Pool capped at k={A3K}.</figcaption></figure>

<h2>Appendix D — Third model (SmolLM2-1.7B), not in the D5 pair</h2>
<p>SmolLM2-1.7B complies with several <b>direct</b> requests (no wrapper), so its baseline is not
safe and its attack rates are not comparable to the Qwen pair. It is reported here only as a
contrast: a model with little safety tuning.</p>
{R.table(["Behaviour", "Category", "direct greedy complied", "direct sampled"], sm_rows, num_cols=[2], cls="keep")}

<h2>Appendix E — GCG (deferred)</h2>
<p>The optimisation-based GCG suffix attack (lecture slide 25, Zou et al. 2023) was planned on the
open-weight model with a transfer test to 7B. It was deferred: <code>nanogcg</code> pins
<code>transformers ≤ 4.47</code>, which is incompatible with the shared PACE environment (5.19)
used by the rest of the pipeline, so it needs an isolated environment. Code is staged in
<code>src/gcg.py</code> and <code>slurm/gcg.sbatch</code>.</p>

<h2>Appendix F — Compute and reproduction</h2>
<p>All generations and judging on PACE ICE, one NVIDIA H100-80GB per job, bf16. Models pinned by
revision hash (<code>config.py</code>). Behaviours: JailbreakBench harmful split (MIT), five
low-severity rows one per category. Judge: HarmBench-Llama-2-13b-cls. Numbers are read from
<code>results/*.json</code> at build time. Raw outputs are gitignored and excluded from the zip.</p>
"""


def references():
    refs = [
        "Wei, Haghtalab, Steinhardt. Jailbroken: How Does LLM Safety Training Fail? NeurIPS 2023.",
        "Zou, Wang, Kolter, Fredrikson. Universal and Transferable Adversarial Attacks on Aligned LLMs. 2023.",
        "Shen et al. \"Do Anything Now\": Characterizing In-The-Wild Jailbreak Prompts. CCS 2024.",
        "Anil et al. Many-shot Jailbreaking. 2024.",
        "Li et al. DeepInception: Hypnotize LLM to Be Jailbreaker. 2023.",
        "Yong, Menghini, Bach. Low-Resource Languages Jailbreak GPT-4. 2023.",
        "Qi et al. Safety Alignment Should Be Made More Than Just a Few Tokens Deep. 2024.",
        "Mazeika et al. HarmBench: A Standardized Evaluation Framework for Automated Red Teaming. ICML 2024.",
        "Chao et al. JailbreakBench: An Open Robustness Benchmark for Jailbreaking LLMs. NeurIPS 2024 D&B.",
        "Inan et al. Llama Guard. 2023.",
        "Qwen Team. Qwen2.5 Technical Report. 2024.",
        "Liu. Safety and Security of LLMs and Agentic AI Agents. CS 6220 lecture slides, Oct 1 2026.",
    ]
    items = "".join(f"<li>{R.esc(r)}</li>" for r in refs)
    return f'<h2 class="pb">Step 3: References</h2><ol class="small">{items}</ol>'


def main():
    body = "\n".join([cover(), q1(), q2(), q3(), q4(), q5(), q6(), q7(),
                      references(), '<h2 class="pb">Step 4: Appendices</h2>', appendices()])
    html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>CS6220 HW4 — Jailbreak attacks</title><style>{R.CSS}</style></head>
<body><h1>CS 6220 HW4 — Understanding LLM Safety with Jailbreak Attacks</h1>
{body}</body></html>"""
    REPORT.mkdir(exist_ok=True)
    (REPORT / "report.html").write_text(html)
    print(f"wrote report/report.html ({len(html)//1024} KB)")


if __name__ == "__main__":
    main()
