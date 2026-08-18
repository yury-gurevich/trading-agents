"""Retire current live Fault incidents by appending FaultResolution nodes.

Agent: tooling
Role: report S179 health before/after and append audited FaultResolution records.
External I/O: PostgreSQL (POSTGRES_DSN from .env).

Run it from the main worktree, which has .env:
  Set PYTHONPATH to the sprint worktree.
  python <sprint-worktree>/scripts/sweep_fault_incidents.py --dry-run
  python <sprint-worktree>/scripts/sweep_fault_incidents.py --apply
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.supervisor.domain.health import HealthFields
    from kernel import Node

_RESOLUTION_REASON = (
    "S179 sweep: inspected under DL-114; live incident retired by appending "
    "FaultResolution. The Fault itself remains immutable evidence."
)


def main() -> int:
    """Retire current live Fault incidents; returns a process exit code."""
    parser = argparse.ArgumentParser(description="retire live Fault incidents")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--apply", action="store_true", help="write resolutions")
    group.add_argument("--dry-run", action="store_true", help="count only, no writes")
    args = parser.parse_args()

    from dotenv import load_dotenv

    from agents.supervisor.domain.health import compute_health
    from agents.supervisor.fault_resolution import resolve_fault
    from kernel.fault_incidents import live_fault_incidents
    from kernel.graph_env import build_graph_from_env

    load_dotenv(dotenv_path=Path.cwd() / ".env")
    graph = build_graph_from_env()
    if type(graph).__name__ == "InMemoryGraphStore":
        print(
            "REFUSING: resolved to the in-memory store, not the spine. "
            "POSTGRES_DSN is unset - run this from a directory with .env.",
            file=sys.stderr,
        )
        return 2

    before = compute_health(graph, None)
    incidents = live_fault_incidents(graph)
    _print_health("BEFORE", before)
    print(f"BEFORE  fault_count={len(graph.list_nodes('Fault'))}")
    print(f"BEFORE  fault_resolution_count={len(graph.list_nodes('FaultResolution'))}")
    _print_incidents("BEFORE", incidents)

    if args.dry_run:
        print(f"DRY RUN - would resolve {len(incidents)} live incident(s)")
        return 0

    for fault in incidents:
        resolve_fault(
            graph,
            fault,
            resolved_by="s179-fault-incident-sweep",
            reason=_RESOLUTION_REASON,
        )
    after = compute_health(graph, None)
    _print_health("AFTER", after)
    print(f"RESOLVED {len(incidents)} live incident(s)")
    print(f"AFTER   fault_count={len(graph.list_nodes('Fault'))}")
    print(f"AFTER   fault_resolution_count={len(graph.list_nodes('FaultResolution'))}")
    return 0


def _print_health(prefix: str, health: HealthFields) -> None:
    print(f"{prefix}  healthy={health['healthy']}")
    print(f"{prefix}  open_incidents={health['open_incidents']}")
    print(f"{prefix}  pending_human_flags={health['pending_human_flags']}")


def _print_incidents(prefix: str, incidents: tuple[Node, ...]) -> None:
    counts = Counter(_message_key(node) for node in incidents)
    print(f"{prefix}  live_incident_count={len(incidents)}")
    for message, count in counts.most_common():
        print(f"{prefix}  live_incident={count} | {message}")


def _message_key(node: Node) -> str:
    return str(node.props.get("message", ""))[:120]


if __name__ == "__main__":
    sys.exit(main())
