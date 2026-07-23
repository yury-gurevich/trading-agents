"""Fault sink that persists every fault as a graph node.

Agent: kernel
Role: make swallowed faults survive the process that produced them.
External I/O: GraphStore writes via the injected backend.

A ``fault_boundary(..., reraise=False)`` keeps a run alive when a step fails, but with
an in-memory sink the fault dies with the container and the run still reads clean. The
07-20 close dispatch failed exactly that way: a stop-out decision reached no broker and
left no trace. Wrapping the sink writes the evidence before it can be lost.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel.errors import AgentFault, FaultSink
    from kernel.graph import GraphStore

FAULT_LABEL = "Fault"


class GraphFaultSink:
    """FaultSink decorator that appends one ``Fault`` node before forwarding."""

    def __init__(self, graph: GraphStore, inner: FaultSink) -> None:
        """Wrap an existing fault sink with graph persistence."""
        self.graph = graph
        self.inner = inner

    def submit(self, fault: AgentFault) -> None:
        """Persist and forward one fault."""
        self.graph.merge_node(FAULT_LABEL, fault_node_key(fault), _fault_props(fault))
        self.inner.submit(fault)


def fault_node_key(fault: AgentFault) -> str:
    """Build the stable node key for one fault.

    Keyed by origin plus timestamp so a repeated failure appends rather than
    overwriting the earlier occurrence — a fault that recurs every run is itself
    the signal.
    """
    return (
        f"fault:{fault.source_agent}:{fault.source_module}"
        f":{fault.capability or 'none'}:{fault.occurred_at.isoformat()}"
    )


def _fault_props(fault: AgentFault) -> dict[str, object]:
    return {
        "source_agent": fault.source_agent,
        "source_module": fault.source_module,
        "capability": fault.capability,
        "severity": fault.severity,
        "error_type": fault.error_type,
        "message": fault.message,
        "traceback": fault.traceback,
        "correlation_id": fault.correlation_id,
        "occurred_at": fault.occurred_at.isoformat(),
        "status": "pending",
    }
