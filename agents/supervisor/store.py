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


def write_flag(
    graph: GraphStore,
    *,
    subject_ref: str,
    severity: str,
    reason: str,
    status: str = "pending",
) -> Node:
    """Write one idempotent human-review flag node."""
    key = _flag_key(subject_ref, severity)
    current = graph.get_node("Flag", key)
    if current is not None:
        return current
    return graph.merge_node(
        "Flag",
        key,
        {
            "subject_ref": subject_ref,
            "severity": severity,
            "reason": reason,
            "status": status,
            "created_at": datetime.now(tz=UTC).isoformat(),
        },
    )


def resolve_flag(graph: GraphStore, subject_ref: str, severity: str) -> Node | None:
    """Append a FlagResolution node linked to the existing Flag, if present."""
    flag_node = graph.get_node("Flag", _flag_key(subject_ref, severity))
    if flag_node is None:
        return None
    key = _resolution_key(subject_ref, severity)
    current = graph.get_node("FlagResolution", key)
    if current is not None:
        return current
    resolution = graph.merge_node(
        "FlagResolution",
        key,
        {
            "subject_ref": subject_ref,
            "severity": severity,
            "resolved_at": datetime.now(tz=UTC).isoformat(),
        },
    )
    graph.add_edge(resolution, flag_node, "RESOLVES")
    return resolution


def resolve_flag_by_subject(graph: GraphStore, subject_ref: str) -> bool:
    """Resolve the first unresolved Flag matching ``subject_ref``."""
    if not subject_ref:
        return False
    for flag_node in graph.list_nodes("Flag"):
        if flag_node.props.get("subject_ref") != subject_ref:
            continue
        severity = str(flag_node.props.get("severity", "critical"))
        key = _resolution_key(subject_ref, severity)
        if graph.get_node("FlagResolution", key) is not None:
            continue
        return resolve_flag(graph, subject_ref, severity) is not None
    return False


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


def _flag_key(subject_ref: str, severity: str) -> str:
    return f"flag:{subject_ref}:{severity}"


def _resolution_key(subject_ref: str, severity: str) -> str:
    return f"resolution:{_flag_key(subject_ref, severity)}"
