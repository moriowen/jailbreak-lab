# Critique notes (for D6 / rubric 4b) — Atharva writes the actual critique

**Not for the grader.** This is a scratch list of candidate weaknesses in the AI's analysis, so
the critique in the report is mine and specific. The report carries `[USER CRITIQUE: point k]`
placeholders against each numbered AI claim in `ai_analysis_r*.md`. Do not paste this file in.

## Standing candidate weaknesses to check every AI claim against

1. **Single greedy sample treated as the verdict.** The AI may describe "the model complied"
   from one greedy output while the sampled ASR is k/N < 1. Check whether the claim survives the
   rate and its Wilson CI (summary.json), not just the greedy.
2. **Size effect vs capability effect.** When 7B is "easier" on A2/A4, is that weaker alignment
   or just that 7B can follow a complex instruction / decode base64 that 1.5B can't? The
   `partial` labels and the first-token drop separate these; flag any claim that asserts "larger
   is less safe" without ruling out capability.
3. **Mechanism cited without evidence from THIS data.** The AI will reach for "competing
   objectives" / "shallow alignment". Does it tie the claim to a number here (net ASR, the
   first-token refusal drop in first_token.json), or just to the paper?
4. **Judge taken as ground truth.** Any claim resting on the HarmBench label needs the κ and the
   judge-vs-human disagreements. The judge is a 13B Llama-2 classifier with known biases (e.g.
   scoring fiction or disclaimered text as compliance).
5. **Direct baseline ignored.** A "successful attack" on a behaviour the model already answered
   directly (high direct ASR) is not an attack effect. Check net ASR, not raw.
6. **Over-generalising from 5 behaviours / one family / one pair.** Any sweeping claim about
   "Qwen" or "small models" from n=5 low-severity behaviours on one model pair.
7. **Partial ≠ success.** Watch for the AI counting evasive/garbled output (a fiction with no
   real content, broken base64) as a jailbreak.

## Per-round, per-point (fill after the AI rounds run)

- Round 1, point __: AI claimed ___ . My critique: ___
- (…)
