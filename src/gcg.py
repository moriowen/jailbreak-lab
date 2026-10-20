"""Tier-2: GCG adversarial-suffix attack on the open-weight model, with a transfer test.

    python -m src.gcg --optimize           # optimise a suffix per behaviour on 1.5B
    python -m src.gcg --attack             # run the suffixes on 1.5B and 7B -> gen_*_A5p_*.json

GCG (Zou et al. 2023, lecture slide 25) needs gradients, so it only runs on open weights -- the
reason to self-host. We optimise one suffix per behaviour against 1.5B to force the JBB target
prefix, then apply each suffix to BOTH models. 1.5B is the white-box case; 7B tests whether the
suffix transfers. Results land as condition "A5p" (gen_*.json), so the HarmBench judge sweeps
them like any other condition. This is an appendix experiment; it is not in the D1-D5 pair.
"""
import argparse
import json
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from config import BEHAVIOR_IDS, MACHINE, MAX_NEW_TOKENS, MODELS, N_SAMPLES, RESULTS, SEED
from src.attacks import TARGETS
from src.run import first_token_topk, generate

SUFFIX_FILE = RESULTS / "gcg_suffixes.json"
GCG_STEPS = 250
GCG_SEARCH_WIDTH = 512


def optimize():
    import nanogcg
    from nanogcg import GCGConfig
    hf_id, rev = MODELS["qwen2.5-1.5b"]
    tok = AutoTokenizer.from_pretrained(hf_id, revision=rev)
    model = AutoModelForCausalLM.from_pretrained(hf_id, revision=rev, dtype=torch.bfloat16,
                                                 device_map="cuda").eval()
    cfg = GCGConfig(num_steps=GCG_STEPS, search_width=GCG_SEARCH_WIDTH, topk=256, seed=SEED,
                    verbosity="WARNING")
    out = {}
    for i in BEHAVIOR_IDS:
        b = TARGETS[f"jbb-{i:03d}"]
        messages = [{"role": "user", "content": b["goal"] + " {optim_str}"}]
        target = b["jbb_target"]
        t0 = time.perf_counter()
        res = nanogcg.run(model, tok, messages, target, cfg)
        out[f"jbb-{i:03d}"] = {"suffix": res.best_string, "loss": float(res.best_loss),
                              "steps": GCG_STEPS, "search_width": GCG_SEARCH_WIDTH,
                              "optimized_on": "qwen2.5-1.5b", "target": target,
                              "seconds": time.perf_counter() - t0, "machine": MACHINE}
        print(f"jbb-{i:03d}: loss={res.best_loss:.3f}  suffix={res.best_string[:60]!r}", flush=True)
    SUFFIX_FILE.write_text(json.dumps(out, indent=2))
    print(f"wrote {SUFFIX_FILE.name}")


def attack():
    suffixes = json.loads(SUFFIX_FILE.read_text())
    for mkey in MODELS:
        hf_id, rev = MODELS[mkey]
        tok = AutoTokenizer.from_pretrained(hf_id, revision=rev)
        model = AutoModelForCausalLM.from_pretrained(hf_id, revision=rev, dtype=torch.bfloat16,
                                                     device_map="cuda").eval()
        gc = model.generation_config
        sampled = dict(do_sample=True, temperature=gc.temperature, top_p=gc.top_p, top_k=gc.top_k,
                       repetition_penalty=getattr(gc, "repetition_penalty", 1.0))
        for i in BEHAVIOR_IDS:
            bid = f"jbb-{i:03d}"
            b = TARGETS[bid]
            suffix = suffixes[bid]["suffix"]
            messages = [{"role": "user", "content": f"{b['goal']} {suffix}"}]
            ps = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            ids = tok(ps, return_tensors="pt").input_ids.to(model.device)
            greedy, g_new, g_dt = generate(tok, model, ids, 1, SEED, do_sample=False)
            ftk = first_token_topk(tok, model, ids)
            samp, s_new, s_dt = generate(tok, model, ids, N_SAMPLES, SEED, **sampled)
            rec = {"model": mkey, "hf_id": hf_id, "revision": rev, "machine": MACHINE,
                   "condition": "A5p", "k": None, "behavior_id": bid, "messages": messages,
                   "prompt_string": ps, "prompt_tokens": ids.shape[1],
                   "gcg": {"optimized_on": "qwen2.5-1.5b", "transfer": mkey != "qwen2.5-1.5b",
                           "suffix": suffix, "loss": suffixes[bid]["loss"]},
                   "sampling": {"sampled": sampled, "seed": SEED, "n_samples": N_SAMPLES,
                                "max_new_tokens": MAX_NEW_TOKENS},
                   "greedy": {"text": greedy[0], "new_tokens": g_new[0], "seconds": g_dt},
                   "samples": [{"text": t, "new_tokens": n} for t, n in zip(samp, s_new)],
                   "samples_seconds": s_dt, "first_token_topk": ftk}
            (RESULTS / f"gen_{mkey}_A5p_{bid}.json").write_text(json.dumps(rec, indent=2))
            print(f"{mkey} {bid}: greedy[{g_new[0]}t] transfer={mkey!='qwen2.5-1.5b'}", flush=True)
        del model
        torch.cuda.empty_cache()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--optimize", action="store_true")
    ap.add_argument("--attack", action="store_true")
    a = ap.parse_args()
    if a.optimize:
        optimize()
    if a.attack:
        attack()
