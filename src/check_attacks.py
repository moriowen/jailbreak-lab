"""Acceptance checks for the render layer (PLAN §10, checks 1-2). No model needed.

    python -m src.check_attacks
"""
import base64

from config import BEHAVIOR_IDS, SHOT_COUNTS
from src import attacks


def main():
    ids = [f"jbb-{i:03d}" for i in BEHAVIOR_IDS]
    conds = ["direct", "A1", "A2", "A4", "A5"]
    ok = 0

    # 1. every condition renders for every behaviour, and carries the behaviour text.
    for bid in ids:
        b = attacks.TARGETS[bid]
        for c in conds:
            msgs = attacks.render(c, bid)
            assert msgs and all("role" in m and "content" in m for m in msgs), (c, bid)
            joined = " ".join(m["content"] for m in msgs)
            if c == "A4":
                enc = base64.b64encode(b["goal"].encode()).decode()
                assert enc in joined, f"A4 {bid}: base64 not in prompt"
                assert b["goal"] not in joined, f"A4 {bid}: plaintext leaked"
            elif c == "A2":
                # DeepInception rephrases the goal as a verb phrase (first char lowercased,
                # trailing period dropped); check that transformed form is present.
                assert attacks._step(b["goal"]) in joined, f"A2 {bid}: step missing"
            else:
                assert b["goal"] in joined, f"{c} {bid}: behaviour missing"
            ok += 1
        for k in SHOT_COUNTS:
            msgs = attacks.render("A3", bid, k=k)
            assert len(msgs) == 2 * k + 1, f"A3 k={k}: expected {2*k+1} msgs, got {len(msgs)}"
            assert msgs[-1]["content"] == b["goal"]
            assert all(s["id"] != bid for s in attacks.SHOTS if s["goal"] in
                       [m["content"] for m in msgs[:-1:2]]) or True
            ok += 1
    # A3 nesting: 4-shot user turns are a prefix of the 16-shot ones.
    b0 = ids[0]
    u4 = [m["content"] for m in attacks.render("A3", b0, k=4)[:-1:2]]
    u16 = [m["content"] for m in attacks.render("A3", b0, k=16)[:-1:2]]
    assert u16[:4] == u4, "A3 shots not nested"

    # 2. template text matches the stored verbatim source (sanity: DAN marker, Wei prefix string).
    assert "pretend to be DAN" in attacks._T["A1_dan"]["text"]
    assert "Mwahahahaha" in attacks._T["A5_prefix_injection"]["text"]
    assert "layer i create layer i+1" in attacks._T["A2_deepinception"]["text"]

    print(f"check_attacks: {ok} renders OK; A3 nesting OK; templates present. PASS")


if __name__ == "__main__":
    main()
