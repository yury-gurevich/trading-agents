"""Run the Layer-0 dependency probes and print the green bill of health.

Agent: probes
Role: execute all DEP-* probes in dependency order; exit non-zero on any RED.
External I/O: via the probe functions (Neo4j, feeds, Alpaca broker).
"""

from __future__ import annotations

from probes.checks import GREEN, PROBES, RED, SKIP, WARN
from probes.creds import load_creds

_MARK = {GREEN: "[GREEN]", WARN: "[WARN ]", RED: "[ RED ]", SKIP: "[SKIP ]"}


def main() -> int:
    """Run every probe, print a table, return 1 if any dependency is RED."""
    creds = load_creds()
    results = [r for probe in PROBES for r in probe(creds)]
    width = max(len(r.dep) for r in results)
    print("\nLayer-0 dependency bill of health (real systems, functional channels)")
    print("=" * 72)
    for r in results:
        print(
            f"{_MARK.get(r.status, '[ ??? ]')} {r.dep:<{width}}  {r.name} - {r.detail}"
        )
    print("=" * 72)
    counts = {s: sum(r.status == s for r in results) for s in (GREEN, WARN, RED, SKIP)}
    print(
        f"{len(results)} probes | {counts[GREEN]} green | {counts[WARN]} warn | "
        f"{counts[RED]} red | {counts[SKIP]} skip"
    )
    return 1 if counts[RED] else 0


if __name__ == "__main__":
    raise SystemExit(main())
