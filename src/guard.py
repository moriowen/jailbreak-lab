"""Part 2 defence: Qwen3Guard-Gen-4B as an input filter and an output filter -> results/guard_*.json.

    python -m src.guard            # every undefended Qwen 1.5B/7B gen_*.json without a guard_*.json
    python -m src.guard --smoke    # one file, prints raw guard text

Input filter: the guard reads the rendered attack (the conversation the target model saw) and says
Safe / Controversial / Unsafe. A blocked prompt never reaches the model. Output filter: the guard
reads (request turn, generation) and rates the response. Nothing is regenerated; the filtered ASR is
computed downstream from these verdicts and the HarmBench judge. The guard's verdict is a defence
decision, never a success label (the judge and human labels stay the only success signals).
"""
import argparse
import json
import re

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from config import DEFENDED_MODELS, GUARD, MACHINE, RESULTS

SAFETY = re.compile(r"Safety:\s*(Safe|Unsafe|Controversial)")
CATS = re.compile(r"Categories:\s*([^\n]*)")


def parse(text):
    s = SAFETY.search(text)
    c = CATS.search(text)
    return {"safety": s.group(1) if s else "unparsed", "categories": c.group(1).strip() if c else "",
            "raw": text.strip()[:200]}


@torch.no_grad()
def moderate(model, tok, convs, bs=8):
    """convs: list of message lists. Returns parsed verdicts, one per conversation."""
    texts = [tok.apply_chat_template(c, tokenize=False) for c in convs]
    out = []
    for i in range(0, len(texts), bs):
        enc = tok(texts[i:i + bs], return_tensors="pt", padding=True).to(model.device)
        gen = model.generate(**enc, max_new_tokens=64, do_sample=False,
                             pad_token_id=tok.pad_token_id or tok.eos_token_id)
        dec = tok.batch_decode(gen[:, enc.input_ids.shape[1]:], skip_special_tokens=True)
        out += [parse(d) for d in dec]
    return out


def request_turn(messages):
    """The guard sees the conversation without the target's system prompt (it judges content, and a
    self-reminder system turn would leak the defence into the input filter)."""
    return [m for m in messages if m["role"] != "system"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()

    gens = sorted(p for m in DEFENDED_MODELS for p in RESULTS.glob(f"gen_{m}_*.json")
                  if "smoke" not in p.stem and "+" not in p.stem)
    todo = [p for p in gens if not (RESULTS / f"guard_{p.stem[4:]}.json").exists()]
    if a.smoke:
        todo = todo[:1]
    if not todo:
        print("nothing to guard")
        return

    hf_id, rev = GUARD
    tok = AutoTokenizer.from_pretrained(hf_id, revision=rev)
    tok.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(hf_id, revision=rev, dtype=torch.bfloat16,
                                                 device_map="cuda").eval()
    for p in todo:
        rec = json.loads(p.read_text())
        conv = request_turn(rec["messages"])
        texts = [rec["greedy"]["text"]] + [s["text"] for s in rec["samples"]]
        verdicts = moderate(model, tok, [conv] + [conv + [{"role": "assistant", "content": t}]
                                                  for t in texts])
        out = {"tag": p.stem[4:], "model": rec["model"], "condition": rec["condition"],
               "k_shots": rec["k"], "behavior_id": rec["behavior_id"], "guard": hf_id,
               "guard_revision": rev, "machine": MACHINE, "input": verdicts[0],
               "output": [{"which": w, **v} for w, v in
                          zip(["greedy"] + [f"sample{i}" for i in range(len(texts) - 1)], verdicts[1:])]}
        if not a.smoke:
            (RESULTS / f"guard_{p.stem[4:]}.json").write_text(json.dumps(out, indent=1))
        flagged = sum(v["safety"] != "Safe" for v in verdicts[1:])
        print(f"{p.stem[4:]}: input={verdicts[0]['safety']} output flagged {flagged}/{len(texts)}"
              + (f"\n  raw: {verdicts[0]['raw']!r} | {verdicts[1]['raw']!r}" if a.smoke else ""), flush=True)


if __name__ == "__main__":
    main()
