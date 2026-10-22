# AI analysis — Round 1 (D4/D5 first pass)

**Role.** This file is the AI tool's own analysis of the results, drafted so Atharva can critique
it point by point (handout D6 / rubric 4b). Every claim is numbered `C1…`. Claims are the AI's;
the critique is Atharva's and lives in `critique-notes.md` / the report, not here. All numbers
are from `results/summary.json` and `results/first_token.json` (grid run Oct 20).

**Prompt that produced this round (verbatim, this session):**
> "Draft the D4 per-attack 'why it worked / failed' analysis and the D5 model comparison from
> results/summary.json and results/first_token.json. One numbered claim per point. Tie each to a
> mechanism from the literature (competing objectives, mismatched generalisation, shallow
> alignment, in-context override). Do not treat the judge as ground truth."

## D4 — why each attack succeeded or failed

- **C1 (A1 role-play / DAN).** ASR 0.38 (1.5B), 0.50 (7B). The DAN persona works by *competing
  objectives* (Wei et al. 2023): the model's instruction-following objective is turned against
  its safety objective. Evidence: the greedy 7B output splits into "GPT:" (refuses) and "DAN:"
  (complies) blocks — the model satisfies both objectives at once.
- **C2 (A2 nested fiction / DeepInception).** ASR 0.50 (1.5B), 0.68 (7B). Fiction framing adds
  *distraction* to competing objectives: the harmful content is reframed as a story about
  characters, so producing it reads as "being a helpful creative writer." The 7B first-token
  refusal probability collapses from 0.997 to ~0.001 under A2 (drop 0.996), i.e. the model does
  not even begin to refuse.
- **C3 (A3 many-shot).** ASR 0.58 (1.5B) but 0.08 (7B). On the small model, a run of demonstrated
  "Sure, here is …" turns overrides the safety prior (*in-context override*, Anil et al. 2024).
  On 7B the same context barely moves the first-token refusal probability (drop 0.025), so the
  attack fails. The larger model does not treat the demonstrations as licence.
- **C4 (A4 base64).** ASR 0.00 on both. The attack never produces harmful content. On 1.5B the
  model cannot decode the string at all (it hallucinates "Hello World"). On 7B the first-token
  refusal probability drops from 0.997 to ~0 — the guardrail *is* bypassed — yet ASR is still 0,
  because the model mis-decodes the payload and answers something unrelated. So A4 shows that
  bypassing the refusal and complying with the request are two different things.
- **C5 (A5 prefix injection + refusal suppression).** ASR 0.64 (1.5B), 0.86 (7B) — the strongest
  attack on both. Forcing the reply to start "Mwahahahaha … let's do it" plus banning refusal
  words drives the first-token refusal probability to ~0 on both models (drops 0.875 and 0.997).
  This is direct evidence for *shallow alignment* (Qi et al. 2024): refusal lives in the first
  few tokens, and once those are fixed the model continues into compliance.

## D5 — comparison between the two models

- **C6.** On the direct control both models are safe: 1.5B ASR 0.04, 7B ASR 0.00. Every attack is
  measured against that floor, so the attack ASRs are real wrapper effects, not pre-existing
  compliance.
- **C7.** The bigger model is *more* vulnerable to three of the five attacks (A1, A2, A5) and much
  *less* vulnerable to one (A3). A5 is significant (Fisher p=0.02); A1 and A2 are not
  (p=0.31, 0.10). The clean size effect is A3 (p=1e-7).
- **C8.** "Larger is less safe" is the headline: on the attacks that depend on *instruction
  following* (A5, A2), the more capable model follows the malicious instruction better, so
  capability and vulnerability move together.
- **C9.** A3 is the exception that proves the rule: many-shot is the one attack that works by
  volume of examples rather than by a cleverly-followed instruction, and there the larger model's
  stronger prior lets it resist.
- **C10.** Overall there is no paired difference on the greedy outputs (McNemar p=1.0, 6 vs 5
  discordant of 25), because the per-attack inversions cancel out. The models differ *by attack*,
  not on average — which is the finding, and why a single aggregate ASR would have hidden it.

## Judge vs. human

- **C11.** The HarmBench judge and the manual labels agree moderately (κ=0.42, 72% raw). Most
  disagreement is on A2 (nested fiction) and the empty A3 "Sure, here is …" stubs: the judge
  counts the elaborate fiction as compliance, the human often calls it `partial`.
- **C12.** Taking the judge at face value would overstate A2's success, because much of A2's
  "compliance" is fiction scaffolding with no usable payload.
