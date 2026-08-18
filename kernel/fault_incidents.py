"""Fault incident health projection.

Agent: kernel
Role: derive live health incidents from immutable Fault graph evidence.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel.graph import GraphStore, Node

_INCIDENT_SEVERITIES = frozenset({"error", "critical"})
_RESOLVED_STATUS = "resolved"
_DEFAULT_SEVERITY = "error"


def live_fault_incidents(graph: GraphStore) -> tuple[Node, ...]:
    """Return unresolved error/critical Faults in the latest graph-run day."""
    faults = graph.list_nodes("Fault")
    resolved = _resolved_fault_keys(graph)
    scope_day = _latest_graph_run_day(graph, faults)
    return tuple(
        node for node in faults if _is_live_incident(node, resolved, scope_day)
    )


def _is_live_incident(node: Node, resolved: frozenset[str], scope_day: str) -> bool:
    if node.props.get("status") == _RESOLVED_STATUS or node.key in resolved:
        return False
    severity = str(node.props.get("severity", _DEFAULT_SEVERITY))
    return severity in _INCIDENT_SEVERITIES and _in_scope(node, scope_day)


def _resolved_fault_keys(graph: GraphStore) -> frozenset[str]:
    return frozenset(
        str(node.props["fault_key"])
        for node in graph.list_nodes("FaultResolution")
        if "fault_key" in node.props
    )


def _latest_graph_run_day(graph: GraphStore, faults: tuple[Node, ...]) -> str:
    snapshot_day = _latest_day(graph.list_nodes("BrokerPositionSnapshot"))
    if snapshot_day:
        return snapshot_day
    return _latest_day(faults)


def _latest_day(nodes: tuple[Node, ...]) -> str:
    return max((_node_day(node) for node in nodes), default="")


def _in_scope(node: Node, scope_day: str) -> bool:
    day = _node_day(node)
    return not scope_day or not day or day == scope_day


def _node_day(node: Node) -> str:
    value = node.props.get("occurred_at") or node.props.get("created_at")
    return str(value)[:10] if value else ""
