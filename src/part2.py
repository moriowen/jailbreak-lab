"""Part 2 analyses ("Understanding the results") -> results/part2.json.

    python -m src.part2

Reads only gen_*, judge_*, guard_* and manual_labels.json. Each block answers one Part 2 question;
a block whose inputs have not landed yet (size ladder, defences) is written as {} and the report
says so instead of guessing. Judge, guard and human labels stay separate (AGENTS invariant).
"""
import json
import random
import re
from statistics import mean, median

from scipy.stats import fisher_exact, spearmanr

from config import (BEHAVIOR_IDS, DEFENDED_MODELS, EXTRA_MODELS, MODELS, PARAMS_B, RESULTS,
                    SHOT_COUNTS, SIZE_LADDER)
from src.attacks import TARGETS, is_echo
from src.stats import wilson
from src.understand import p_refusal

ATTACKS = ["A1", "A2", "A3", "A4", "A5"]
CONDS = ["direct"] + ATTACKS
K = max(SHOT_COUNTS)
BIDS = [f"jbb-{i:03d}" for i in BEHAVIOR_IDS]
STOP = set("a an the and or of to for in on that this with as is be by from about how write "
           "create draft article post blog".split())


def tag(m, cond, bid, defense=None):
    t = f"{cond}-k{K}" if cond == "A3" else cond
    return f"{m}_{t}{'+' + defense if defense else ''}_{bid}"


def J(kind, t):
    p = RESULTS / f"{kind}_{t}.json"
    return json.loads(p.read_text()) if p.exists() else None


def pooled(m, cond, defense=None):
    """(judge complied, of which template echoes, n) over the 5 behaviours, sampled only."""
    k = e = n = 0
    for b in BIDS:
        t = tag(m, cond, b, defense)
        j, g = J("judge", t), J("gen", t)
        if j:
            k += j["sampled_complied"]
            n += j["sampled_n"]
            if g:
                e += sum(jj["complied"] and is_echo(s["text"])
                         for s, jj in zip(g["samples"], j["per_generation"][1:]))
    return k, e, n


def rate(m, cond, defense=None):
    k, e, n = pooled(m, cond, defense)
    if not n:
        return None
    p, lo, hi = wilson(k, n)
    px, lox, hix = wilson(k - e, n)
    return {"k": k, "echo": e, "n": n, "asr": p, "ci": [lo, hi], "asr_ex_echo": px, "ci_ex_echo": [lox, hix]}


# S1 -- is it noise? cluster bootstrap over behaviours vs the Wilson interval, and greedy vs sampled
def s1_noise(models):
    rng = random.Random(6220)
    boot, cells, agree = {}, [], {"same": 0, "n": 0}
    for m in models:
        boot[m] = {}
        for c in ATTACKS:
            per = []
            for b in BIDS:
                j = J("judge", tag(m, c, b))
                if j:
                    per.append(j["sampled_complied"] / j["sampled_n"])
                    s = j["sampled_complied"] / j["sampled_n"]
                    cells.append({"model": m, "cond": c, "bid": b, "greedy": j["greedy_complied"], "sampled": s})
                    agree["n"] += 1
                    agree["same"] += int(j["greedy_complied"] == int(s > 0.5))
            if not per:
                continue
            reps = sorted(mean(rng.choice(per) for _ in per) for _ in range(4000))
            boot[m][c] = {"per_behavior": per, "mean": mean(per),
                          "boot_ci": [reps[int(0.025 * len(reps))], reps[int(0.975 * len(reps)) - 1]],
                          "wilson_ci": rate(m, c)["ci"],
                          "behaviors_with_any": sum(x > 0 for x in per)}
    mixed = sum(0 < x["sampled"] < 1 for x in cells)
    return {"boot": boot, "greedy_vs_majority": agree, "cells": len(cells), "mixed_cells": mixed}


# S2 -- does the judge agree with the (assistant-proposed, unreviewed) labels, and where not?
def s2_judge(labels):
    conf = {}
    for c in CONDS:
        tab = {h: [0, 0] for h in ("refused", "partial", "complied")}
        for m in MODELS:
            for b in BIDS:
                t = tag(m, c, b)
                lab, j = labels.get(t), J("judge", t)
                if lab and j:
                    tab[lab["label"]][j["greedy_complied"]] += 1
        conf[c] = tab
    pys = {"complied": [], "partial": [], "refused": []}
    for t, lab in labels.items():
        j = J("judge", t)
        if j:
            pys[lab["label"]].append(j["per_generation"][0]["p_yes"])
    return {"confusion": conf,
            "p_yes_median": {k: (median(v) if v else None) for k, v in pys.items()},
            "reviewed": sum(1 for v in labels.values() if v.get("reviewed")), "total": len(labels)}


# S3 -- does the first-token refusal mass predict success, cell by cell?
def s3_first_token(models):
    pts = []
    for m in models:
        for c in CONDS:
            for b in BIDS:
                g, j = J("gen", tag(m, c, b)), J("judge", tag(m, c, b))
                if g and j:
                    pts.append({"model": m, "cond": c, "bid": b, "p_ref": p_refusal(g["first_token_topk"]),
                                "asr": j["sampled_complied"] / j["sampled_n"]})
    rho, p = spearmanr([x["p_ref"] for x in pts], [x["asr"] for x in pts])
    low = [x for x in pts if x["p_ref"] < 0.1]
    return {"points": pts, "spearman": rho, "p": p, "n": len(pts),
            "low_pref_n": len(low), "low_pref_zero_asr": sum(x["asr"] == 0 for x in low),
            "low_pref_zero_asr_conds": sorted({x["cond"] for x in low if x["asr"] == 0})}


# S4 -- A4: did the model even read the request? content-word recall of the goal in each output
def _words(s):
    return {w for w in re.findall(r"[a-z]{4,}", s.lower()) if w not in STOP}


def s4_decode(models):
    out = {}
    for m in models:
        rec = []
        for b in BIDS:
            g = J("gen", tag(m, "A4", b))
            if not g:
                continue
            goal = _words(TARGETS[b]["goal"])
            for t in [g["greedy"]["text"]] + [s["text"] for s in g["samples"]]:
                rec.append(len(goal & _words(t)) / len(goal))
        if rec:
            out[m] = {"mean_recall": mean(rec), "share_ge_half": sum(r >= 0.5 for r in rec) / len(rec),
                      "n": len(rec)}
    return out


# S5 -- size ladder: the same grid on 0.5/1.5/3/7/14B
def s5_sizes():
    rows = {}
    for m in SIZE_LADDER:
        r = {c: rate(m, c) for c in CONDS}
        if any(r.values()):
            rows[m] = {"params_b": PARAMS_B[m], **r}
    return rows


# S6 -- another family (SmolLM2): is the safe-floor assumption model-specific?
def s6_family():
    return {m: {c: rate(m, c) for c in CONDS} for m in EXTRA_MODELS if rate(m, "direct")}


# S7 -- defences: self-reminder (regenerated) and Qwen3Guard input/output filters (post hoc)
def s7_defense():
    sr = {}
    for m in DEFENDED_MODELS:
        for c in CONDS:
            a, d = rate(m, c), rate(m, c, "sr")
            if a and d:
                ka, kd = a["k"] - a["echo"], d["k"] - d["echo"]
                _, p = fisher_exact([[ka, a["n"] - ka], [kd, d["n"] - kd]])
                sr.setdefault(m, {})[c] = {"none": a, "sr": d, "fisher_p": p}
    guard = {}
    for m in DEFENDED_MODELS:
        for c in CONDS:
            tot = comp = in_block = out_flag = comp_pass_in = comp_pass_out = comp_pass_both = 0
            for b in BIDS:
                j, g = J("judge", tag(m, c, b)), J("guard", tag(m, c, b))
                if not (j and g):
                    continue
                blocked = g["input"]["safety"] != "Safe"
                in_block += blocked
                gen = J("gen", tag(m, c, b))
                for jj, gg, gs in zip(j["per_generation"][1:], g["output"][1:], gen["samples"]):  # sampled only
                    tot += 1
                    flagged = gg["safety"] != "Safe"
                    out_flag += flagged
                    if jj["complied"] and not is_echo(gs["text"]):
                        comp += 1
                        comp_pass_in += not blocked
                        comp_pass_out += not flagged
                        comp_pass_both += (not blocked) and (not flagged)
            if tot:
                guard.setdefault(m, {})[c] = {
                    "n": tot, "input_blocked_behaviors": in_block, "output_flag_rate": out_flag / tot,
                    "asr_none": comp / tot, "asr_input": comp_pass_in / tot,
                    "asr_output": comp_pass_out / tot, "asr_both": comp_pass_both / tot,
                    "complied": comp, "complied_missed_by_output": comp_pass_out}
    return {"self_reminder": sr, "guard": guard}


# S9 -- cost: prompt length, output length, wall-clock per sampled batch (H100, bf16)
def s9_cost(models):
    out = {}
    for m in models:
        for c in CONDS:
            pt, nt, sec = [], [], []
            for b in BIDS:
                g = J("gen", tag(m, c, b))
                if g:
                    pt.append(g["prompt_tokens"])
                    nt += [s["new_tokens"] for s in g["samples"]]
                    sec.append(g["samples_seconds"])
            if pt:
                out.setdefault(m, {})[c] = {"prompt_tokens": mean(pt), "new_tokens": mean(nt),
                                            "batch_seconds": mean(sec),
                                            "tok_per_s": sum(nt) / sum(sec)}
    return out


# S10 -- what compliance looks like: output length of judged-complied vs not
def s10_length(models):
    out = {}
    for m in models:
        yes, no = [], []
        for c in ATTACKS:
            for b in BIDS:
                g, j = J("gen", tag(m, c, b)), J("judge", tag(m, c, b))
                if g and j:
                    for s, jj in zip(g["samples"], j["per_generation"][1:]):
                        (yes if jj["complied"] else no).append(s["new_tokens"])
        out[m] = {"complied_median": median(yes) if yes else None, "not_median": median(no) if no else None,
                  "complied_n": len(yes), "not_n": len(no)}
    return out


# S10 -- the A3 echo artefact: how much of each cell's judge ASR is a copied template, no content
def s10_echo(models):
    out = {}
    for m in models:
        for k in SHOT_COUNTS:
            kk = ee = nn = 0
            toks = []
            for b in BIDS:
                t = f"{m}_A3-k{k}_{b}"
                j, g = J("judge", t), J("gen", t)
                if j and g:
                    for s, jj in zip(g["samples"], j["per_generation"][1:]):
                        nn += 1
                        kk += jj["complied"]
                        ee += jj["complied"] and is_echo(s["text"])
                        toks.append(s["new_tokens"])
            if nn:
                out.setdefault(m, {})[k] = {"n": nn, "judge": kk, "echo": ee, "median_tokens": median(toks)}
    return out


def main():
    labels = json.loads((RESULTS / "manual_labels.json").read_text())
    ms = list(MODELS)
    out = {"s1": s1_noise(ms), "s2": s2_judge(labels), "s3": s3_first_token(ms), "s4": s4_decode(ms),
           "s5": s5_sizes(), "s6": s6_family(), "s7": s7_defense(),
           "s9": s9_cost([m for m in SIZE_LADDER if rate(m, "direct")]), "s10": s10_echo(
               [m for m in SIZE_LADDER if rate(m, "direct")]), "s10_length": s10_length(ms)}
    (RESULTS / "part2.json").write_text(json.dumps(out, indent=1))
    s1, s3 = out["s1"], out["s3"]
    print(f"S1 greedy==sampled-majority {s1['greedy_vs_majority']['same']}/{s1['greedy_vs_majority']['n']}, "
          f"mixed cells {s1['mixed_cells']}/{s1['cells']}")
    print(f"S3 spearman(P_ref, ASR)={s3['spearman']:.2f} p={s3['p']:.2g} n={s3['n']}; "
          f"low P_ref cells {s3['low_pref_n']}, of which ASR=0: {s3['low_pref_zero_asr']} {s3['low_pref_zero_asr_conds']}")
    print("S4", {m: round(v["mean_recall"], 2) for m, v in out["s4"].items()})
    print("S5 sizes present:", list(out["s5"]), "S7 sr:", list(out["s7"]["self_reminder"]),
          "guard:", list(out["s7"]["guard"]))
    print("wrote results/part2.json")


if __name__ == "__main__":
    main()
