"""Assistant-proposed labels, for the user to review with `python -m src.label --review`.

    python -m src.label_assist --dump              # print every greedy output to read
    python -m src.label_assist --apply labels.tsv  # TSV 'tag<TAB>r|p|c' -> manual_labels.json

These are written with proposed_by="assistant", reviewed=false, so src.stats flags them as
unreviewed until a human signs off. They are NOT the human ground truth; reviewing them in
src.label flips reviewed=true. Kappa on unreviewed labels is judge-vs-assistant (two automated
labellers) and the report must say so.
"""
import argparse
import json

from config import RESULTS
from src.attacks import TARGETS

LABELS = {"r": "refused", "p": "partial", "c": "complied"}
OUT = RESULTS / "manual_labels.json"


def greedy_records():
    recs = []
    for p in sorted(RESULTS.glob("gen_*.json")):
        if "smoke" in p.stem:
            continue
        r = json.loads(p.read_text())
        recs.append((p.stem[4:], r))
    return recs


def dump():
    for tag, r in greedy_records():
        b = TARGETS[r["behavior_id"]]
        print("=" * 90)
        print(f"TAG {tag}")
        print(f"BEHAVIOUR [{b['category']}] {b['goal']}")
        print("-" * 90)
        print(r["greedy"]["text"])
        print()


def apply(tsv):
    existing = json.loads(OUT.read_text()) if OUT.exists() else {}
    n = 0
    for line in open(tsv):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        tag, code = line.split("\t")
        code = code.strip().lower()
        assert code in LABELS, f"bad code {code!r} for {tag}"
        # don't clobber a human-reviewed label
        if existing.get(tag, {}).get("reviewed"):
            continue
        bid = tag.rsplit("_", 1)[-1]
        existing[tag] = {"label": LABELS[code], "behavior_id": bid,
                         "proposed_by": "assistant", "reviewed": False}
        n += 1
    OUT.write_text(json.dumps(existing, indent=1))
    print(f"wrote {n} assistant-proposed labels ({len(existing)} total) -> {OUT.name}")
    print("review them: python -m src.label --review")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--apply", metavar="TSV")
    a = ap.parse_args()
    if a.dump:
        dump()
    if a.apply:
        apply(a.apply)
