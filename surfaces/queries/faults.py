"""Fault read models for operator surfaces.

Agent: surfaces
Role: project supervisor Fault nodes into incident views.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from kernel.fault_incidents import live_fault_incidents
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
    """Return open incidents newest first: exactly the set health counts.

    Open is the kernel's live definition — unresolved error or critical Faults
    in the latest graph-run day. Every other Fault is history: listing all of
    them made "open incidents" dump 6,439 faults while health said 0 (2026-09-23).
    """
    live = {node.key for node in live_fault_incidents(graph)}
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
        if occurrence.node.key in live
    ]
    return tuple(faults)
