"""Is every number in every packet defined by the book? (operator rule: ALL quant numbers are interpreted)"""

from __future__ import annotations

import json
from pathlib import Path

from ..laws import required_numbers
from .entries import lookup

CASES = Path(__file__).parents[1] / "cases" / "synthetic"


def main() -> int:
    undefined: set[str] = set()
    for f in sorted(CASES.glob("*.json")):
        c = json.loads(f.read_text())
        for name, text in (
            ("production", c["context"]),
            ("complete", c["context"] + "\n" + c.get("supplement", "")),
        ):
            req = required_numbers(text)
            miss = sorted(k for k in req if lookup(k) is None)
            undefined |= set(miss)
            print(
                f"{c['name']:24s} {name:10s} numbers {sum(len(g) for g in req.values()):3d}  undefined {miss}"
            )
    print("ALL DEFINED" if not undefined else f"UNDEFINED: {sorted(undefined)}")
    return 1 if undefined else 0


if __name__ == "__main__":
    raise SystemExit(main())
