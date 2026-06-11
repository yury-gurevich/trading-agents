"""System health read model.

Agent: surfaces
Role: project graph health signals without calling agents or the bus.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from surfaces.queries._graph import nodes_by_label

if TYPE_CHECKING:
    from kernel import GraphStore, Node


@dataclass(frozen=True)
class HealthSummary:
    """Surface summary of graph-observed system health."""

    healthy: bool
    open_faults: int
    pending_flags: int
    last_run_id: str | None


def system_health(graph: GraphStore) -> HealthSummary:
    """Project graph state into a health summary without calling the bus."""
    open_faults = sum(
        1
        for node in nodes_by_label(graph, "Fault")
        if node.props.get("status") != "resolved"
    )
    pending_flags = _pending_flag_count(graph)
    critical_flags = _pending_flag_count(graph, severity="critical")
    return HealthSummary(
        healthy=open_faults == 0 and critical_flags == 0,
        open_faults=open_faults,
        pending_flags=pending_flags,
        last_run_id=_last_run_id(graph),
    )


def _pending_flag_count(graph: GraphStore, severity: str | None = None) -> int:
    resolved = {_flag_ref(node) for node in nodes_by_label(graph, "FlagResolution")}
    count = 0
    for flag in nodes_by_label(graph, "Flag"):
        if severity is not None and flag.props.get("severity") != severity:
            continue
        if flag.props.get("status") != "resolved" and _flag_ref(flag) not in resolved:
            count += 1
    return count


def _flag_ref(node: Node) -> tuple[str, str]:
    return (
        str(node.props.get("subject_ref", node.key)),
        str(node.props.get("severity", "")),
    )


def _last_run_id(graph: GraphStore) -> str | None:
    snapshots = nodes_by_label(graph, "Snapshot")
    if not snapshots:
        return None
    latest = max(
        snapshots,
        key=lambda node: str(node.props.get("created_at", node.key)),
    )
    return str(latest.props.get("run_id", latest.key.removeprefix("snapshot:")))
