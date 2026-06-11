"""Supervisor graph write path.

Agent: supervisor
Role: write dispatcher message lineage and captured agent faults.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from contracts.common import Provenance

if TYPE_CHECKING:
    from kernel import AgentFault, GraphStore, Node


def write_message(
    graph: GraphStore, *, run_id: str, step_name: str, status: str
) -> Node:
    """Write one idempotent dispatcher step message node."""
    key = f"{run_id}:{step_name}"
    props = {"run_id": run_id, "step": step_name, "status": status}
    if graph.get_node("Message", key) is None:
        props["created_at"] = datetime.now(tz=UTC).isoformat()
    return graph.merge_node("Message", key, props)


def write_fault(
    graph: GraphStore,
    fault: AgentFault,
    *,
    run_id: str | None = None,
    max_message_chars: int,
) -> Node:
    """Write one idempotent fault node keyed by source and message digest."""
    message = fault.message[:max_message_chars]
    key = _fault_key(fault, run_id, message)
    props = {
        "run_id": run_id,
        "source_agent": fault.source_agent,
        "source_module": fault.source_module,
        "capability": fault.capability,
        "severity": fault.severity,
        "error_type": fault.error_type,
        "message": message,
        "correlation_id": fault.correlation_id,
    }
    if graph.get_node("Fault", key) is None:
        props["occurred_at"] = fault.occurred_at.isoformat()
        props["created_at"] = datetime.now(tz=UTC).isoformat()
    return graph.merge_node("Fault", key, props)


def write_dispatch_run(
    graph: GraphStore,
    *,
    run_id: str,
    steps_attempted: tuple[str, ...],
    completed: bool,
    faults: tuple[AgentFault, ...],
    max_fault_message_chars: int,
) -> Provenance:
    """Write all step messages and run faults for one dispatcher outcome."""
    status = "completed" if completed else "attempted"
    first: Node | None = None
    for step_name in steps_attempted:
        node = write_message(graph, run_id=run_id, step_name=step_name, status=status)
        first = node if first is None else first
    for fault in faults:
        node = write_fault(
            graph, fault, run_id=run_id, max_message_chars=max_fault_message_chars
        )
        first = node if first is None else first
    return Provenance(
        run_id=run_id,
        source_agent="supervisor",
        graph_node_id=None if first is None else f"{first.label}:{first.key}",
    )


def _fault_key(fault: AgentFault, run_id: str | None, message: str) -> str:
    digest = hashlib.sha256(message.encode("utf-8")).hexdigest()[:12]
    scope = run_id or fault.correlation_id or "unscoped"
    capability = fault.capability or "unknown"
    return (
        f"{scope}:{fault.source_agent}:{fault.source_module}:"
        f"{capability}:{fault.error_type}:{digest}"
    )
