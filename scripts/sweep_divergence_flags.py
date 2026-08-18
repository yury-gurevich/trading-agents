"""Retire the pre-S178 snapshot-keyed divergence flags — append-only.

Agent: tooling
Role: append one FlagResolution per legacy `broker-position-divergence` Flag and
      report pending_human_flags before and after. Never edits, deletes or
      rewrites a Flag, Position or any broker state (DL-44).
External I/O: PostgreSQL (POSTGRES_DSN from .env).

Run it:
  PYTHONPATH=. python scripts/sweep_divergence_flags.py --dry-run
  PYTHONPATH=. python scripts/sweep_divergence_flags.py --apply
"""

from __future__ import annotations

import argparse
import sys

_REASON = (
    "S178 sweep: raised at run start before adoption was attempted, and the "
    "divergence it named was adopted from broker truth in the same run. Retired "
    "by appending this resolution; the Flag itself is untouched."
)


def main() -> int:
    """Sweep legacy divergence flags; returns a process exit code."""
    parser = argparse.ArgumentParser(description="retire legacy divergence flags")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--apply", action="store_true", help="write the resolutions")
    group.add_argument("--dry-run", action="store_true", help="count only, no writes")
    args = parser.parse_args()

    from dotenv import load_dotenv

    from agents.execution.reconciliation_flags import resolve_legacy_flags
    from agents.supervisor.domain.health import compute_health
    from kernel.graph_env import build_graph_from_env

    load_dotenv()
    graph = build_graph_from_env()
    if type(graph).__name__ == "InMemoryGraphStore":
        print(
            "REFUSING: resolved to the in-memory store, not the spine. "
            "POSTGRES_DSN is unset - run this from a directory with .env.",
            file=sys.stderr,
        )
        return 2

    before = compute_health(graph, None)
    print(f"BEFORE  healthy={before['healthy']}")
    print(f"BEFORE  pending_human_flags={before['pending_human_flags']}")

    if args.dry_run:
        print("DRY RUN - no resolutions written")
        return 0

    resolved = resolve_legacy_flags(graph, reason=_REASON)
    after = compute_health(graph, None)
    print(f"RESOLVED {len(resolved)} legacy divergence flags")
    print(f"AFTER   healthy={after['healthy']}")
    print(f"AFTER   pending_human_flags={after['pending_human_flags']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
