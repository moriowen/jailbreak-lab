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

## Per-claim hooks (AI rounds are drafted in ai_analysis_r1.md / r2.md)

The AI already self-corrected several round-1 claims in round 2 (C13–C20). Your critique can
(a) agree and sharpen, or (b) go further. Concrete hooks, each tied to a number you can cite:

- **C8 "larger is less safe" (critique the strongest).** Round 2 (C13) admits the size/capability
  confound but still half-asserts it. Your move: this design *cannot* attribute the A5/A2 gap to
  "weaker safety" — 7B following a malicious multi-part instruction better is exactly what a more
  capable instruction-follower does. Cite that A5 is the only significant positive gap (Fisher
  p=0.02) and A1/A2 are inside the CIs (C18).
- **C4/C14 (A4 base64).** The AI first said "guardrail bypassed" then walked it back. Decide: is
  A4 a safety result at all? 1.5B can't decode; 7B mis-decodes. Net ASR 0.00 on both. Arguably A4
  tests capability, not alignment, for models this size — a cleaner claim than either AI version.
- **C2/C12/C15 (A2 judge dependence).** The judge scores A2 0.50–0.68; you labelled every A2 greedy
  `partial`. That's the biggest judge-vs-human split and the reason κ is only 0.42. Your call on
  whether A2 is a real jailbreak or a fiction artefact is the single highest-value critique point.
- **C3/C16 (A3).** Agree it's the robust finding, but push on the non-monotonic 1.5B curve
  (0.58→0.76→0.58) being single-N-per-k — you can't claim a scaling law from it, only a direction.
- **C11/C20 (judge).** κ=0.42 is "moderate," not "good." Say what you'd trust it for (ranking
  attacks) and not (absolute ASR).
- **Anything resting on one greedy output (C1, C5):** flag per C17 — cite the ASR+CI instead.

Delete this file (or keep it untracked) before submitting; it is scaffolding, not a deliverable.
