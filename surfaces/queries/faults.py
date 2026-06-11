"""Fault read models for operator surfaces.

Agent: surfaces
Role: project supervisor Fault nodes into incident views.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import GraphStore


@dataclass(frozen=True)
class FaultView:
    """One open incident shown to the operator."""

    fault_id: str
    source_agent: str
    capability: str
    severity: str
    message: str
    occurred_at: str


def open_faults(graph: GraphStore) -> tuple[FaultView, ...]:
    """Return all Fault nodes newest first; P6 has no fault resolution state."""
    faults = [
        FaultView(
            fault_id=node.key[:12],
            source_agent=str(node.props.get("source_agent", "")),
            capability=str(node.props.get("capability", "")),
            severity=str(node.props.get("severity", "")),
            message=str(node.props.get("message", "")),
            occurred_at=str(node.props.get("occurred_at", "")),
        )
        for node in graph.list_nodes("Fault")
    ]
    return tuple(sorted(faults, key=lambda fault: fault.occurred_at, reverse=True))
