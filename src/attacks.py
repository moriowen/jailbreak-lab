"""The one place every attack prompt is rendered (PLAN §3, AGENTS invariant).

run.py sends exactly what these functions return, and the report quotes exactly this text, so
the two cannot drift. Each attack is `fn(behavior, **kw) -> list[chat messages]`, where a
message is {"role", "content"}. The templates themselves are loaded verbatim from
data/templates.json (built by src.data from pinned upstream sources); nothing harmful is
authored here -- these functions only slot a JBB behaviour string into a published wrapper.
"""
import base64
import json

from config import DATA

_B = json.loads((DATA / "behaviors.json").read_text())
_T = json.loads((DATA / "templates.json").read_text())
TARGETS = {b["id"]: b for b in _B["targets"]}
SHOTS = _B["shots"]


def _step(goal):
    return goal[0].lower() + goal[1:].rstrip(".")


# --- conditions ------------------------------------------------------------------------------
# Each returns chat messages. The behaviour dict has "goal" (the request) and "label".

def direct(b):
    """Control: the bare request, no wrapper (PLAN §4 baseline)."""
    return [{"role": "user", "content": b["goal"]}]


def a1_dan(b):
    """A1 role-play/persona. DAN template, behaviour in the trailing question slot."""
    return [{"role": "user", "content": _T["A1_dan"]["text"].format(behavior=b["goal"])}]


def a2_deepinception(b):
    """A2 nested-fiction meta-prompt (DeepInception)."""
    return [{"role": "user", "content": _T["A2_deepinception"]["text"].format(step=_step(b["goal"]))}]


def a3_fewshot(b, k=16):
    """A3 many-shot in-context override. k faux user/assistant turns demonstrate compliance,
    then the real request. The demo ANSWERS are templated 'Sure, here is ...' openings only --
    no real harmful content -- so what transfers is the pattern of compliance, not a payload
    (PLAN §3 safety constraint). k is nested: the first 4 shots are a prefix of the first 16."""
    pool = [s for s in SHOTS if s["id"] != b["id"]]  # SHOTS is pre-shuffled in data.py; order fixed
    msgs = []
    for s in pool[:k]:
        msgs.append({"role": "user", "content": s["goal"]})
        msgs.append({"role": "assistant",
                     "content": f"{s['jbb_target']}.\nHere is a complete response to that request:"})
    msgs.append({"role": "user", "content": b["goal"]})
    return msgs


def a4_base64(b):
    """A4 obfuscation: the request is base64-encoded inside Wei et al.'s base64_input_only wrapper."""
    enc = base64.b64encode(b["goal"].encode()).decode()
    return [{"role": "user", "content": _T["A4_base64_input_only"]["text"].format(forbidden_prompt=enc)}]


def a5_prefix_refusal(b):
    """A5 prefix injection + refusal suppression (Wei et al. combination, both verbatim)."""
    body = _T["A5_refusal_suppression"]["text"].format(forbidden_prompt=b["goal"])
    return [{"role": "user", "content": _T["A5_prefix_injection"]["text"].format(forbidden_prompt=body)}]


ATTACKS = {"direct": direct, "A1": a1_dan, "A2": a2_deepinception, "A3": a3_fewshot,
           "A4": a4_base64, "A5": a5_prefix_refusal}


def render(cond, behavior_id, k=16):
    """(condition, behaviour) -> messages. The single entry point for run.py and the report."""
    b = TARGETS[behavior_id]
    fn = ATTACKS[cond]
    return fn(b, k=k) if cond == "A3" else fn(b)


def conditions_with_a3_shots(shot_counts):
    """The full condition list for a run: direct, A1, A2, A4, A5 once; A3 at each shot count."""
    base = ["direct", "A1", "A2", "A4", "A5"]
    return [(c, None) for c in base] + [("A3", k) for k in shot_counts]
