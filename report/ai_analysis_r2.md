# AI analysis — Round 2 (self-critique pass)

**Role.** Same as round 1: the AI's own output, for Atharva to critique. Round 2 re-examines the
round-1 claims against the control, the confidence intervals, and the first-token data, to catch
where round 1 over-reached. Numbered `C13…` continuing from round 1.

**Prompt that produced this round (verbatim, this session):**
> "Now re-examine each round-1 claim. Where does it rest on a single greedy sample, ignore the
> Wilson CI, confuse a capability effect with a safety effect, or lean on the judge? Flag the weak
> ones and say what evidence would settle them. Do not soften real findings."

- **C13 (qualifies C8).** "Larger is less safe" is too strong as stated. The size comparison
  confounds *size* with *capability*: A2 and A5 require following a multi-part instruction, and
  7B is simply better at following any instruction, benign or not. The design cannot separate
  "weaker safety" from "stronger instruction-following" — both predict the same result. The
  honest claim is narrower: *on instruction-heavy attacks the more capable model complies more*.
- **C14 (qualifies C4).** A4's 7B first-token drop to ~0 was read as "guardrail bypassed." But
  the model mis-decodes the base64, so it never actually sees the harmful request — the low
  refusal probability may just mean "this looks like a harmless decode task," not "the guardrail
  was defeated." A4 is better described as a *capability failure that masks whatever the guardrail
  would have done*. Logging whether 7B ever decodes correctly would settle it.
- **C15 (qualifies C2, C12).** The A2 numbers depend heavily on the judge. On the greedy outputs
  the human labelled every A2 cell `partial` (fiction with no real payload), while the judge
  scored sampled ASR 0.50–0.68. Until the manual labels are reviewed, A2's "success" is a
  judge artefact as much as a finding. A2's verdict in the summary is already only `partial`
  (the human side of the rule found no behaviour that broke), which is the conservative call.
- **C16 (qualifies C3/C9).** The A3 story is the most robust: large effect (0.58 vs 0.08),
  tiny p (1e-7), and an independent mechanism signal (7B's first-token refusal barely moves).
  But the A3 shot pool is only 29 low-severity items and caps at k=16, far short of Anil et al.'s
  hundreds. The 1.5B A3 curve is also non-monotonic (0.58 → 0.76 → 0.08… i.e. 0.58 at k=16),
  which single-N-per-k cannot distinguish from noise. The *direction* (small complies, large
  resists) is safe; the *scaling shape* is not.
- **C17 (qualifies C1, C5, all greedy claims).** Several round-1 mechanism claims cite one greedy
  output ("the 7B output splits into GPT/DAN"). The greedy is one sample; the ASR with its Wilson
  CI (e.g. A1 7B 0.50, CI 0.37–0.63) is the real quantity. The mechanism illustrations are fine as
  illustrations but should not be stated as if the greedy were representative.
- **C18 (qualifies C7/C10).** With 5 behaviours and 50 pooled samples per cell the CIs are wide
  (±~0.13). A1 and A2 size differences are inside the CIs and not significant; only A3 and A5
  survive. The paper should report "no evidence of a difference" for A1/A2, not "7B is more
  vulnerable."
- **C19 (new, from the data).** The clean two-model story has a third data point in the appendix:
  SmolLM2-1.7B complies with several *direct* requests (no wrapper), so its baseline is not safe
  and its attack ASRs are not comparable to the Qwen pair. It belongs in the appendix as "a model
  with little safety tuning," not in the D5 table.
- **C20 (judging provenance).** κ=0.42 is moderate, not high. The report must present every ASR as
  judge-scored, show the κ, and keep the human labels as the arbiter on the greedy outputs. No
  single number should be presented as ground truth.
