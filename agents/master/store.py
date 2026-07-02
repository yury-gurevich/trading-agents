"""Master agent Neo4j graph writes — operational registry.

Agent: master
Role: write AgentDefinition, AgentInstance, Session, and CapabilityGrant nodes.
External I/O: Neo4j database via injected GraphStore.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from contracts.master import AgentState

if TYPE_CHECKING:
    from agents.master.remediation import RemediationPlan
    from agents.master.remediation_execution import RemediationAttempt
    from kernel import GraphStore
    from kernel.graph import Node


def write_session(graph: GraphStore, session_id: str) -> Node:
    """Record a new master boot session in the graph."""
    return graph.merge_node(
        "Session",
        session_id,
        {"started_at": datetime.now(UTC).isoformat(), "shutdown_reason": ""},
    )


def write_agent_definition(
    graph: GraphStore,
    agent_type: str,
    capability_schema: dict[str, object],
) -> Node:
    """Upsert a static AgentDefinition node (immutable agent charter)."""
    import json

    return graph.merge_node(
        "AgentDefinition",
        f"def:{agent_type}",
        {
            "agent_type": agent_type,
            "capability_schema": json.dumps(capability_schema, sort_keys=True),
        },
    )


def write_agent_instance(
    graph: GraphStore,
    instance_id: str,
    agent_type: str,
    boot_id: str,
    state: AgentState = AgentState.ACTIVE,
) -> Node:
    """Record a live agent instance in the fleet registry."""
    return graph.merge_node(
        "AgentInstance",
        instance_id,
        {
            "agent_type": agent_type,
            "boot_id": boot_id,
            "state": state.value,
            "started_at": datetime.now(UTC).isoformat(),
        },
    )


def write_escalation(
    graph: GraphStore,
    agent_type: str,
    failed_credentials: tuple[str, ...],
    mode: str = "manual",
) -> Node:
    """Record a credential-test failure that blocked an agent's activation (DL-36).

    Open until a human (or, later, an automatic remediation) resolves it. ``mode`` and
    ``auto_attempts`` are the one-shot structure the remediation loop (C/D) consumes.
    """
    ts = datetime.now(UTC)
    key = f"escalation:{agent_type}:{ts.strftime('%Y%m%dT%H%M%S%f')}"
    return graph.merge_node(
        "Escalation",
        key,
        {
            "agent_type": agent_type,
            "failed_credentials": list(failed_credentials),
            "mode": mode,
            "auto_attempts": 0,
            "status": "open",
            "created_at": ts.isoformat(),
        },
    )


def write_remediation_plan(
    graph: GraphStore,
    escalation_key: str,
    plan: RemediationPlan,
) -> Node:
    """Record the bounded LLM remediation plan for an escalation."""
    escalation = graph.get_node("Escalation", escalation_key)
    if escalation is None:
        raise KeyError(f"no Escalation with key {escalation_key!r}")
    ts = datetime.now(UTC)
    node = graph.merge_node(
        "RemediationPlan",
        f"remediation-plan:{escalation_key}:{ts.strftime('%Y%m%dT%H%M%S%f')}",
        {
            "escalation_key": escalation_key,
            "remediation": plan.remediation,
            "rationale": plan.rationale,
            "auto_eligible": plan.auto_eligible,
            "status": plan.status,
            "created_at": ts.isoformat(),
        },
    )
    graph.add_edge(escalation, node, "PLANNED_BY")
    return node


def write_remediation_attempt(
    graph: GraphStore,
    escalation_key: str,
    attempt: RemediationAttempt,
) -> Node:
    """Record an automatic remediation attempt for an escalation."""
    escalation = graph.get_node("Escalation", escalation_key)
    if escalation is None:
        raise KeyError(f"no Escalation with key {escalation_key!r}")
    ts = datetime.now(UTC)
    node = graph.merge_node(
        "RemediationAttempt",
        f"remediation-attempt:{escalation_key}:{ts.strftime('%Y%m%dT%H%M%S%f')}",
        {
            "escalation_key": escalation_key,
            "agent_type": str(escalation.props.get("agent_type", "")),
            "failed_credentials": list(escalation.props.get("failed_credentials", ())),
            "remediation": attempt.remediation,
            "status": attempt.status,
            "message": attempt.message,
            "executor": attempt.executor,
            "auto": attempt.auto,
            "created_at": ts.isoformat(),
        },
    )
    graph.add_edge(escalation, node, "ATTEMPTED_BY")
    return node


def write_escalation_remediation_outcome(
    graph: GraphStore,
    escalation_key: str,
    attempt: RemediationAttempt,
    *,
    resolved: bool,
) -> Node:
    """Append the remediation outcome without overwriting the original escalation."""
    if graph.get_node("Escalation", escalation_key) is None:
        raise KeyError(f"no Escalation with key {escalation_key!r}")
    ts = datetime.now(UTC).isoformat()
    return graph.merge_node(
        "Escalation",
        escalation_key,
        {
            "resolution_status": "resolved" if resolved else "open",
            "mode_after_remediation": "" if resolved else "manual",
            "auto_attempts_used": 1 if attempt.auto else 0,
            "last_remediation_status": attempt.status,
            "last_remediation_at": ts,
        },
    )


def write_capability_grant(
    graph: GraphStore,
    instance_id: str,
    capability: str,
    config: dict[str, object],
) -> Node:
    """Record what capabilities master granted to an agent instance."""
    import json

    key = f"grant:{instance_id}:{capability}"
    return graph.merge_node(
        "CapabilityGrant",
        key,
        {
            "instance_id": instance_id,
            "capability": capability,
            "config": json.dumps(config, sort_keys=True),
            "granted_at": datetime.now(UTC).isoformat(),
        },
    )
