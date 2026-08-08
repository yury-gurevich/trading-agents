"""Fault read models for operator surfaces.

Agent: surfaces
Role: project supervisor Fault nodes into incident views.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from kernel.fault_query import fault_occurrences

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
    occurrence_count: int = 1
    suppressed_count: int = 0


def open_faults(graph: GraphStore) -> tuple[FaultView, ...]:
    """Return all Fault nodes newest first; P6 has no fault resolution state."""
    faults = [
        FaultView(
            fault_id=occurrence.node.key[:12],
            source_agent=str(occurrence.node.props.get("source_agent", "")),
            capability=str(occurrence.node.props.get("capability", "")),
            severity=str(occurrence.node.props.get("severity", "")),
            message=str(occurrence.node.props.get("message", "")),
            occurred_at=occurrence.occurred_at.isoformat(),
            occurrence_count=occurrence.occurrence_count,
            suppressed_count=occurrence.suppressed_count,
        )
        for occurrence in fault_occurrences(graph)
    ]
    return tuple(faults)
