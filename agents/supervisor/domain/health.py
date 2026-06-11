"""Supervisor health graph queries.

Agent: supervisor
Role: derive live system health from Fault, Flag, and Snapshot graph nodes.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from kernel import GraphStore, Node


class HealthFields(TypedDict):
    """Raw graph-derived health fields used by MasterReport."""

    healthy: bool
    open_incidents: int
    pending_human_flags: int
    last_successful_run: str | None


def compute_health(graph: GraphStore, run_id: str | None) -> HealthFields:
    """Return raw health fields for a MasterReport."""
    del run_id
    faults = graph.list_nodes("Fault")
    flags = graph.list_nodes("Flag")
    resolutions = graph.list_nodes("FlagResolution")
    snapshots = graph.list_nodes("Snapshot")
    open_incidents = sum(1 for node in faults if node.props.get("status") != "resolved")
    resolved_keys = {_resolution_key(node) for node in resolutions}
    critical_flags = sum(
        1
        for node in flags
        if _resolution_key(node) not in resolved_keys
        and node.props.get("severity") == "critical"
    )
    latest = _latest_snapshot(snapshots)
    return {
        "healthy": open_incidents == 0 and critical_flags == 0,
        "open_incidents": open_incidents,
        "pending_human_flags": critical_flags,
        "last_successful_run": None if latest is None else latest.key,
    }


def _latest_snapshot(snapshots: tuple[Node, ...]) -> Node | None:
    if not snapshots:
        return None
    return max(
        snapshots,
        key=lambda node: str(node.props.get("created_at", node.key)),
    )


def _resolution_key(node: Node) -> tuple[str, str]:
    return (str(node.props.get("subject_ref")), str(node.props.get("severity")))
