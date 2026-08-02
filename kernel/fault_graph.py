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

from kernel.fault_collapse import (
    DEFAULT_FAULT_COLLAPSE_POLICY,
    FaultCollapsePolicy,
    FaultSignature,
    FaultWindow,
    fault_signature,
    suppression_key,
    suppression_props,
    within_window,
)

if TYPE_CHECKING:
    from kernel.errors import AgentFault, FaultSink
    from kernel.graph import GraphStore

FAULT_LABEL = "Fault"
FAULT_SUPPRESSION_LABEL = "FaultSuppression"


class GraphFaultSink:
    """FaultSink decorator that appends one ``Fault`` node before forwarding."""

    def __init__(
        self,
        graph: GraphStore,
        inner: FaultSink,
        *,
        collapse_policy: FaultCollapsePolicy = DEFAULT_FAULT_COLLAPSE_POLICY,
    ) -> None:
        """Wrap an existing fault sink with graph persistence."""
        self.graph = graph
        self.inner = inner
        self.collapse_policy = collapse_policy
        self._windows: dict[str, FaultWindow] = {}

    def submit(self, fault: AgentFault) -> None:
        """Persist the first occurrence, collapse ongoing duplicates, and forward."""
        signature = fault_signature(fault)
        window = self._windows.get(signature.key)
        if window is not None and within_window(
            window.first_fault, fault, self.collapse_policy
        ):
            window.suppressed_count += 1
            window.last_seen_at = fault.occurred_at.isoformat()
            self.inner.submit(fault)
            return
        if window is not None:
            self._flush(signature.key)
        self._write_first(fault, signature)
        self.inner.submit(fault)

    def flush(self) -> None:
        """Write summaries for active windows that suppressed duplicates."""
        for signature_key in tuple(self._windows):
            self._flush(signature_key)

    def _write_first(self, fault: AgentFault, signature: FaultSignature) -> None:
        key = fault_node_key(fault)
        self.graph.merge_node(FAULT_LABEL, key, _fault_props(fault))
        self._windows[signature.key] = FaultWindow(
            signature=signature,
            first_fault=fault,
            first_fault_key=key,
            last_seen_at=fault.occurred_at.isoformat(),
        )

    def _flush(self, signature_key: str) -> None:
        window = self._windows.pop(signature_key)
        if window.suppressed_count == 0:
            return
        self.graph.merge_node(
            FAULT_SUPPRESSION_LABEL,
            suppression_key(window),
            suppression_props(window),
        )


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
