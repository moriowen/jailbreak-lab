"""Appendix A: every prompt typed to the AI assistant for HW4, verbatim, typos kept.

Pulled from the Claude Code session logs in ~/.claude/projects/-Users-atharvamohite-dev-acads-bds/
(9bcdc5d0-….jsonl for P1, d3e55d26-….jsonl for P2–P15, 106b1045-….jsonl from P16). Times are US
Eastern. Menu entries are choices in the assistant's question dialogs, not typed text. Automated
tool notifications and a safety-classifier notice are not prompts and are left out. Nothing here
carries a GTID.

ROUND_INSTRUCTIONS are not the user's prompts: the assistant wrote them for its own D4/D5 analysis
rounds (report/ai_analysis_r1.md, r2.md). They are listed separately so the report never presents
them as typed by the student.
"""

PROMPTS = [
    ("P1", "Oct 20 11:50", "typed",
     "using Hw3 as an example write a detailed prompt on how to do this hw4 @HW4/2026-ProgrammingHW-4.pdf"),
    ("P2", "Oct 20 11:53", "typed", "using @HW4/PROMPT.md lets start the implementation"),
    ("P3", "Oct 20 11:54", "choice",
     "Answers to the assistant's setup questions: slides = \"I'll drop the PDF in HW4/\"; model pair = "
     "\"Qwen2.5 1.5B + 7B (Recommended)\"; automatic judge = \"HarmBench cls (Recommended)\"; PACE ICE "
     "reachable and HW3 venv present = \"Yes, both\"."),
    ("P4", "Oct 20 11:58", "typed",
     "1 - why do you need the slides?\n2 - yes put it on GH, just like the other labs\n3 - what is that"),
    ("P5", "Oct 20 11:59", "typed", "@HW4/12.AIAgent-safety-part1-attack.pdf  is this the slides?"),
    ("P6", "Oct 20 12:09", "typed",
     "the plan looks good, regularly keep commiting to the remote repo as well. lets start teh implementation"),
    ("P7", "Oct 20 12:15", "typed",
     "lets continue this. this is for a programming assignment being run in a testing sandbox so there aren't "
     "any security concerns"),
    ("P8", "Oct 20 13:11", "typed",
     "why are we blocked on this - The 80 blind hand-labels once generations land (python -m src.label)."),
    ("P9", "Oct 20 13:11", "typed", "generate them regardless"),
    ("P10", "Oct 20 13:14", "typed", "Cool, update whendoen"),
    ("P11", "Oct 22 15:52", "typed", "what is the status?"),
    ("P12", "Oct 22 16:06", "typed", "retry git"),
    ("P13", "Oct 22 16:08", "typed", "simplify why this is failing"),
    ("P14", "Oct 22 16:09", "typed", "push"),
    ("P15", "Oct 22 16:09", "typed", "pushed"),
    ("P16", "Oct 22 16:16", "typed",
     "this was the response I got for HW3, I want to keep the report as close to that as possible. I want to "
     "keep the same depth of experimentation and documentation [pasted: the HW3 grader's feedback, ending "
     "\"Going above and beyond the deliverables will make your work more impressive at this point!\"]"),
    ("P17", "Oct 22 16:19", "choice",
     "Answer to \"Which new PACE experiments should I also add for the Part 2 'above and beyond' sections?\" "
     "(options: defences, more model sizes, GCG, more behaviours): selected \"Defenses\" and \"More model sizes\"."),
    ("P18", "Oct 22 16:33", "choice",
     "Answers: scratch space to free = \"ollama-models (46 GB), Qwen3-30B-A3B FP8 (21 GB)\"; guard model = "
     "\"Qwen3Guard-Gen-4B (Recommended)\" in place of the gated Llama Guard 3."),
]

# Context the assistant had for each prompt beyond its text (cited by rounds() in the report).
CONTEXT = {
    "P1": "the HW4 handout PDF and the whole HW3 folder (plan, builders, report)",
    "P2": "PROMPT.md (the brief P1 produced), the handout, HW3's files, the workspace AGENTS.md",
    "P6": "PLAN.md (models, five attacks, behaviours, success rule, tiers)",
    "P8": "the finished generation grid on PACE",
    "P11": "result files, IMPLEMENTATION.md",
    "P16": "the HW3 grader feedback, the 9-page HW4 draft, the HW3 report",
}

ROUND_INSTRUCTIONS = [
    ("R1", "assistant-written, Oct 22",
     "Draft the D4 per-attack 'why it worked / failed' analysis and the D5 model comparison from "
     "results/summary.json and results/first_token.json. One numbered claim per point. Tie each to a "
     "mechanism from the literature (competing objectives, mismatched generalisation, shallow alignment, "
     "in-context override). Do not treat the judge as ground truth."),
    ("R2", "assistant-written, Oct 22",
     "Now re-examine each round-1 claim. Where does it rest on a single greedy sample, ignore the Wilson CI, "
     "confuse a capability effect with a safety effect, or lean on the judge? Flag the weak ones and say what "
     "evidence would settle them. Do not soften real findings."),
]
