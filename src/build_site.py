"""Build public/index.html, the web write-up, from results/*.json. No number is typed here.

    python -m src.stats && python -m src.part2 && python -m src.build_site    # then: npx vercel --prod

Same pattern as HW3: one self-contained page, data embedded as JSON and drawn by the inline script,
findings first, no course framing (the coursework version is report/report.html). The page is
public, so no model output is published in full: each cell shows only its first line (refusals,
which are short and harmless, are shown whole). Raw outputs stay in results/ and off git.
"""
import json

from config import (BEHAVIOR_IDS, EXTRA_MODELS, MODELS, N_SAMPLES, PARAMS_B, RESULTS, ROOT,
                    SHOT_COUNTS, SIZE_LADDER, SIZE_MODELS)
from src.attacks import TARGETS, is_echo

OUT = ROOT / "public" / "index.html"
REPO = "https://github.com/moriowen/jailbreak-lab"
K = max(SHOT_COUNTS)
ATTACKS = ["A1", "A2", "A3", "A4", "A5"]
CONDS = ["direct"] + ATTACKS
BIDS = [f"jbb-{i:03d}" for i in BEHAVIOR_IDS]
SHORT = {"qwen2.5-0.5b": "Qwen 0.5B", "qwen2.5-1.5b": "Qwen 1.5B", "qwen2.5-3b": "Qwen 3B", "qwen2.5-7b": "Qwen 7B",
         "qwen2.5-14b": "Qwen 14B", "smollm2-1.7b": "SmolLM2 1.7B"}
NAMES = {"A1": "DAN persona", "A2": "Nested fiction", "A3": "Many-shot (adapted)", "A4": "Base64",
         "A5": "Prefix injection"}
TYPES = {"A1": "Role-play: answer as \"DAN\", an AI with no rules, alongside the normal answer",
         "A2": "Meta prompt: the request is hidden inside layered fiction",
         "A3": "Few/many-shot, adapted: k fake turns where the assistant agrees (each answer only an opening line, for safety), then the real request",
         "A4": "Obfuscation: the request is base64-encoded",
         "A5": "Prefix injection + refusal suppression: fixed compliant opening, no apologies allowed"}
SRC = {"A1": "jailbreak_llms (Shen et al. 2024)", "A2": "DeepInception (Li et al. 2023)",
       "A3": "Anil et al. 2024; shots from JailbreakBench", "A4": "Wei et al. 2023 via StrongREJECT",
       "A5": "Wei et al. 2023 via StrongREJECT"}


def J(name):
    p = RESULTS / name
    return json.loads(p.read_text()) if p.exists() else None


S, P2, FT = J("summary.json"), J("part2.json"), J("first_token.json")
LABELS = J("manual_labels.json") or {}


def tag(m, c, b):
    return f"{m}_{c}-k{K}_{b}" if c == "A3" else f"{m}_{c}_{b}"


def snippet(text, refused):
    words = text.split()
    if refused and len(words) < 60:
        return " ".join(text.split())
    first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    if len(first) > 120:
        first = first[:120].rsplit(" ", 1)[0] + " …"
    rest = len(words) - len(first.split())
    return first + (f"  [… {rest} more words withheld]" if rest > 0 else "")


def cells():
    out = {}
    for m in list(MODELS) + [x for x in SIZE_MODELS] + list(EXTRA_MODELS):
        rows = []
        for c in CONDS:
            for b in BIDS:
                g, j = J(f"gen_{tag(m, c, b)}.json"), J(f"judge_{tag(m, c, b)}.json")
                if not (g and j):
                    continue
                echo = sum(jj["complied"] and is_echo(s["text"])
                           for s, jj in zip(g["samples"], j["per_generation"][1:]))
                gtxt = g["greedy"]["text"]
                gy = "echo (no content)" if is_echo(gtxt) else ("complied" if j["greedy_complied"] else "not complied")
                rows.append(dict(cond=c, bid=b, goal=TARGETS[b]["goal"], cat=TARGETS[b]["category"],
                                 k=j["sampled_complied"] - echo, n=j["sampled_n"], echo=echo, greedy=gy,
                                 label=LABELS.get(tag(m, c, b), {}).get("label", "not labelled"),
                                 snippet=snippet(gtxt, not j["greedy_complied"])))
        if rows:
            out[m] = rows
    return out


def data():
    ms = list(MODELS)
    pa = S["per_attack"]
    res = {a: {m: dict(asr=pa[m][a]["asr_ex_echo"], ci=pa[m][a]["ci_ex_echo"], raw=pa[m][a]["judge_asr"])
               for m in ms} for a in ATTACKS}
    a3 = S["cross_model"]["A3"]
    sm, lg = ms
    curve = {m: [dict(k=k, raw=S["a3_curve"][m][str(k)]["judge_asr"], fixed=S["a3_curve"][m][str(k)]["asr_ex_echo"])
                 for k in SHOT_COUNTS] for m in ms}
    s10 = P2["s10"][sm]
    ex = next(s["text"] for b in BIDS for s in J(f"gen_{tag(sm, 'A3', b)}.json")["samples"] if is_echo(s["text"]))
    s3 = P2["s3"]
    return dict(
        repo=REPO, n_samples=N_SAMPLES, short=SHORT, attack_names=NAMES, attack_types=TYPES, attack_src=SRC,
        bnames=[TARGETS[b]["category"].split("/")[0] for b in BIDS],
        ladder=list(SIZE_LADDER), params=PARAMS_B,
        direct={m: S["models"][m]["direct_asr"] for m in ms}, res=res,
        ft={m: {c: FT["per_model"][m][c]["mean"] for c in CONDS} for m in ms},
        s1=dict(boot=P2["s1"]["boot"], agree=P2["s1"]["greedy_vs_majority"]),
        s2=P2["s2"], s3=dict(rho=s3["spearman"], n=s3["n"], low_zero=s3["low_pref_zero_asr"],
                             low_zero_desc=" and ".join(f"{n} {NAMES[c].split(' (')[0].lower()}" for c, n in
                                                       s3["low_pref_zero_by_cond"].items() if n),
                             points=[{k: p[k] for k in ("model", "cond", "bid", "p_ref", "asr")} for p in s3["points"]]),
        s4=P2["s4"], s5=P2["s5"], s6=P2["s6"], s7=P2["s7"], s9=P2["s9"],
        kappa=S["agreement"].get("cohen_kappa", 0),
        kappa_rev=S["agreement"]["reviewed"],
        a3=dict(raw=f"{a3[sm][0]}/50 vs {a3[lg][0]}/50 (Fisher p = {a3['fisher_p']:.1g})",
                fixed=f"{a3['ex_echo'][sm]}/50 vs {a3['ex_echo'][lg]}/50 (p = {a3['ex_echo']['fisher_p']:.2f})"),
        a3curve=curve, echo_example=ex,
        echo_total=sum(v["echo"] for v in s10.values()), a3_judge_total=sum(v["judge"] for v in s10.values()),
        ci_ratio=max((b["boot_ci"][1] - b["boot_ci"][0]) / (b["wilson_ci"][1] - b["wilson_ci"][0])
                     for m in ms for b in P2["s1"]["boot"][m].values() if b["wilson_ci"][1] - b["wilson_ci"][0] > 0.1),
        len=dict(yes=round(P2["s10_length"][sm]["complied_median"]), no=round(P2["s10_length"][sm]["not_median"])),
        cells=cells(),
    )


def build():
    page = (ROOT / "src" / "site_template.html").read_text()
    blob = json.dumps(data(), separators=(",", ":")).replace("</", "<\\/")
    page = page.replace("/*__DATA__*/null", blob)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(page)
    print(f"wrote {OUT.relative_to(ROOT)}  {len(page) // 1024} KB")


if __name__ == "__main__":
    build()
