"""Append-only FaultResolution writes.

Agent: supervisor
Role: retire immutable Fault records by appending resolution evidence.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import GraphStore, Node


def resolve_fault(
    graph: GraphStore, fault: Node, *, resolved_by: str, reason: str
) -> Node:
    """Append one FaultResolution for ``fault`` and link it with RESOLVES."""
    key = fault_resolution_key(fault.key)
    current = graph.get_node("FaultResolution", key)
    if current is not None:
        return current
    resolution = graph.merge_node(
        "FaultResolution",
        key,
        {
            "fault_key": fault.key,
            "resolved_at": datetime.now(tz=UTC).isoformat(),
            "resolved_by": resolved_by,
            "resolution_reason": reason,
        },
    )
    graph.add_edge(resolution, fault, "RESOLVES")
    return resolution


def fault_resolution_key(fault_key: str) -> str:
    """Return the idempotent FaultResolution key for one Fault node."""
    return f"resolution:fault:{fault_key}"
