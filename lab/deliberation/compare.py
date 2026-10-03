"""Compare several runs side by side: python -m lab.deliberation.compare RUN_DIR [RUN_DIR ...]"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from .book.entries import lookup
from .laws import NON_MARKET_PILLARS


def summary(run_dir: str) -> dict:
    d = json.loads((Path(run_dir) / "results.json").read_text())
    first, final = Counter(), Counter()
    rulings, market, read0, read1, need = {}, 0, 0, 0, 0
    directions: dict[tuple[str, str], set[str]] = defaultdict(set)
    for r in d["results"]:
        rl = r["ruling"] or {}
        rulings[r["case"]] = rl.get("ruling", "FAILED")
        market += any(
            lookup(k) and lookup(k).pillar not in NON_MARKET_PILLARS for k in rl.get("decisive", [])
        )
        for s in r["seats"]:
            a0, af = s["attempts"][0], s["attempts"][-1]
            first.update(v["clause"] for v in a0["violations"])
            final.update(v["clause"] for v in af["violations"])
            miss = {
                id(a): next(
                    (len(v["metric"].split(",")) for v in a["violations"] if v["clause"] == "DEC-FORM-07"), 0
                )
                for a in (a0, af)
            }
            need += r["required_numbers"]
            read0 += r["required_numbers"] - miss[id(a0)] if a0["output"] else 0
            read1 += r["required_numbers"] - miss[id(af)] if af["output"] else 0
            out = af["output"] or {}
            for x in out.get("readings", []) + out.get("own_readings", []):
                directions[(r["case"], x["metric"])].add(x["direction"])
    shared = [v for v in directions.values()]
    agree = sum(1 for v in shared if len(v) == 1)
    return {
        "name": d["variant"]["name"],
        "rulings": rulings,
        "market_basis": f"{market}/{len(d['results'])}",
        "coverage": f"{read0 / need:.0%} -> {read1 / need:.0%}" if need else "-",
        "violations": f"{sum(first.values())} -> {sum(final.values())}",
        "agreement": f"{agree}/{len(shared)}",
        "usd": d["cost"]["usd"],
        "calls": d["cost"]["calls"],
    }


def main() -> None:
    rows = [summary(p) for p in sys.argv[1:]]
    print(
        "| Variant | numbers read (first -> retry) | violations | market basis | same direction across seats | calls | $ |"
    )
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        print(
            f"| {r['name']} | {r['coverage']} | {r['violations']} | {r['market_basis']} | {r['agreement']} "
            f"| {r['calls']} | {r['usd']} |"
        )
    cases = sorted({c for r in rows for c in r["rulings"]})
    print("\n| Case | " + " | ".join(r["name"] for r in rows) + " |")
    print("| --- |" + " --- |" * len(rows))
    for c in cases:
        print(f"| {c} | " + " | ".join(r["rulings"].get(c, "-") for r in rows) + " |")


if __name__ == "__main__":
    main()
