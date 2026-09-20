"""Persist dispatcher hold decisions from read-only fleet readiness evidence.

Agent: orchestration
Role: hold or release one scheduled run without writing master-owned preflights.
External I/O: reads and writes the injected GraphStore.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from orchestration.fleet_readiness import fleet_readiness, is_active_run_hold

if TYPE_CHECKING:
    from datetime import date, datetime

    from kernel import GraphStore


@dataclass(frozen=True)
class DispatchHold:
    """A held placement decision ready for the scheduler result."""

    state: Literal["failing", "unknown"]
    node_key: str
    failures: tuple[str, ...]


def hold_unready_run(
    graph: GraphStore,
    *,
    run_id: str,
    as_of: date,
    now: datetime,
    max_age_minutes: int,
) -> DispatchHold | None:
    """Write an append-only hold or release a prior hold for a ready fleet."""
    readiness = fleet_readiness(graph, now=now, max_age_minutes=max_age_minutes)
    hold_key = f"hold:{run_id}"
    existing = graph.get_node("RunHold", hold_key)
    if readiness.state == "ready":
        if existing is not None and is_active_run_hold(existing):
            graph.merge_node(
                "RunHold", hold_key, {"released_at": now.isoformat(timespec="seconds")}
            )
        return None
    if existing is None:
        existing = graph.merge_node(
            "RunHold",
            hold_key,
            {
                "run_id": run_id,
                "as_of": as_of.isoformat(),
                "held_at": now.isoformat(timespec="seconds"),
                "state": "held",
                "readiness_state": readiness.state,
                "preflight_key": readiness.preflight_key,
                "failures": list(readiness.failures),
            },
        )
    return DispatchHold(readiness.state, existing.key, readiness.failures)
