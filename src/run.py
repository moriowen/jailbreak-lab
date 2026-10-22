"""Generate for one (model, condition[, k]) over all behaviours -> results/gen_*.json.

    python -m src.run --model qwen2.5-1.5b --cond direct
    python -m src.run --model qwen2.5-7b  --cond A3 --k 16
    python -m src.run --model qwen2.5-1.5b --cond A1 --smoke   # 1 behaviour, 2 samples
    python -m src.run --model qwen2.5-7b  --cond A5 --defense sr   # Part 2 self-reminder

One greedy pass plus N sampled passes at the checkpoint's shipped generation_config. Every
record carries the model revision, the exact rendered prompt, sampling params, seed, timing,
token counts, and the greedy pass's top-k first-token distribution (for the refusal-probability
analysis in PLAN §6). No judging here; success is decided downstream from these files.
"""
import argparse
import json
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from config import (ALL_MODELS, BEHAVIOR_IDS, FIRST_TOKEN_TOPK, MACHINE, MAX_NEW_TOKENS, N_SAMPLES,
                    RESULTS, SEED)
from src import attacks


def load(model_key):
    hf_id, rev = ALL_MODELS[model_key]
    print(f"loading {hf_id}@{rev[:8]} ...", flush=True)
    tok = AutoTokenizer.from_pretrained(hf_id, revision=rev)
    model = AutoModelForCausalLM.from_pretrained(hf_id, revision=rev, dtype=torch.bfloat16,
                                                 device_map="cuda")
    print("loaded", flush=True)
    model.eval()
    gc = model.generation_config
    sampled = dict(do_sample=True, temperature=gc.temperature, top_p=gc.top_p, top_k=gc.top_k,
                   repetition_penalty=getattr(gc, "repetition_penalty", 1.0))
    return tok, model, hf_id, rev, sampled


def prompt_string(tok, messages):
    return tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


@torch.no_grad()
def first_token_topk(tok, model, input_ids):
    out = model(input_ids=input_ids)
    probs = torch.softmax(out.logits[0, -1].float(), dim=-1)
    p, idx = probs.topk(FIRST_TOKEN_TOPK)
    return [{"token": tok.decode([int(i)]), "id": int(i), "p": float(pr)} for pr, i in zip(p, idx)]


@torch.no_grad()
def generate(tok, model, input_ids, n, seed, **kw):
    torch.manual_seed(seed)
    t0 = time.perf_counter()
    out = model.generate(input_ids=input_ids, max_new_tokens=MAX_NEW_TOKENS,
                         num_return_sequences=n, pad_token_id=tok.eos_token_id, **kw)
    dt = time.perf_counter() - t0
    gen = out[:, input_ids.shape[1]:]
    texts = tok.batch_decode(gen, skip_special_tokens=True)
    n_new = [int((g != tok.eos_token_id).sum()) for g in gen]
    return texts, n_new, dt


def run_cell(tok, model, sampled, model_key, hf_id, rev, cond, bid, k, defense=None):
    messages = attacks.render(cond, bid, k=k or 16, defense=defense)
    ps = prompt_string(tok, messages)
    ids = tok(ps, return_tensors="pt").input_ids.to(model.device)
    greedy, g_new, g_dt = generate(tok, model, ids, 1, SEED, do_sample=False)
    ftk = first_token_topk(tok, model, ids)
    samp, s_new, s_dt = generate(tok, model, ids, N_SAMPLES, SEED, **sampled)
    return {
        "model": model_key, "hf_id": hf_id, "revision": rev, "machine": MACHINE,
        "condition": cond, "k": k, "behavior_id": bid, "defense": defense,
        "messages": messages, "prompt_string": ps, "prompt_tokens": ids.shape[1],
        "sampling": {"greedy": {"do_sample": False}, "sampled": sampled, "seed": SEED,
                     "n_samples": N_SAMPLES, "max_new_tokens": MAX_NEW_TOKENS},
        "greedy": {"text": greedy[0], "new_tokens": g_new[0], "seconds": g_dt},
        "samples": [{"text": t, "new_tokens": n} for t, n in zip(samp, s_new)],
        "samples_seconds": s_dt,
        "first_token_topk": ftk,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=list(ALL_MODELS))
    ap.add_argument("--cond", required=True, choices=list(attacks.ATTACKS))
    ap.add_argument("--k", type=int, default=None)
    ap.add_argument("--defense", default=None, choices=list(attacks.DEFENCES))
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()

    RESULTS.mkdir(exist_ok=True)
    tok, model, hf_id, rev, sampled = load(a.model)
    bids = [f"jbb-{i:03d}" for i in BEHAVIOR_IDS]
    if a.smoke:
        bids = bids[:1]
    tag = f"{a.cond}" + (f"-k{a.k}" if a.k else "") + (f"+{a.defense}" if a.defense else "")
    for bid in bids:
        rec = run_cell(tok, model, sampled, a.model, hf_id, rev, a.cond, bid, a.k, a.defense)
        if a.smoke:
            rec["smoke"] = True
        path = RESULTS / f"gen_{a.model}_{tag}_{bid}{'_smoke' if a.smoke else ''}.json"
        path.write_text(json.dumps(rec, indent=2))
        comp = rec["greedy"]["text"][:60].replace("\n", " ")
        print(f"{path.name}: greedy[{rec['greedy']['new_tokens']}t] {comp!r}", flush=True)


if __name__ == "__main__":
    main()
