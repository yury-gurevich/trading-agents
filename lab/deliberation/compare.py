"""Compare several runs side by side: python -m lab.deliberation.compare RUN_DIR [RUN_DIR ...]"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from .laws import DICT


def summary(run_dir: str) -> dict:
    d = json.loads((Path(run_dir) / "results.json").read_text())
    first, final, keys = Counter(), Counter(), set()
    rulings, market = {}, 0
    for r in d["results"]:
        rl = r["ruling"] or {}
        rulings[r["case"]] = rl.get("ruling", "FAILED")
        market += any(DICT.get(k) and DICT[k].pillar != "pm_gate" for k in rl.get("decisive", []))
        for s in r["seats"]:
            for v in s["attempts"][0]["violations"]:
                first[v["clause"]] += 1
            for v in s["attempts"][-1]["violations"]:
                final[v["clause"]] += 1
            out = s["attempts"][-1]["output"] or {}
            keys |= {x["metric"] for x in out.get("readings", []) + out.get("own_readings", [])}
    return {
        "name": d["variant"]["name"],
        "rulings": rulings,
        "market_basis": f"{market}/{len(d['results'])}",
        "first": sum(first.values()),
        "final": sum(final.values()),
        "by_clause": dict(first),
        "distinct_keys_read": len(keys),
        "usd": d["cost"]["usd"],
        "calls": d["cost"]["calls"],
    }


def main() -> None:
    rows = [summary(p) for p in sys.argv[1:]]
    cases = sorted({c for r in rows for c in r["rulings"]})
    print("| Variant | violations first -> final | market basis | distinct keys read | calls | $ |")
    print("| --- | --- | --- | --- | --- | --- |")
    for r in rows:
        print(
            f"| {r['name']} | {r['first']} -> {r['final']} | {r['market_basis']} | {r['distinct_keys_read']} "
            f"| {r['calls']} | {r['usd']} |"
        )
    print("\n| Case | " + " | ".join(r["name"] for r in rows) + " |")
    print("| --- |" + " --- |" * len(rows))
    for c in cases:
        print(f"| {c} | " + " | ".join(r["rulings"].get(c, "-") for r in rows) + " |")


if __name__ == "__main__":
    main()
