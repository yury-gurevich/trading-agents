"""Supervisor intent gate.

Agent: supervisor
Role: enforce hard-NO, confirmation, and capability-matrix routing in order.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.supervisor.domain.hard_no import is_hard_no
from agents.supervisor.domain.matrix import CAPABILITY_MATRIX, not_available_reason
from agents.supervisor.result import provenance, rejected
from agents.supervisor.store import (
    resolve_flag,
    resolve_flag_by_subject,
    write_flag,
    write_message,
)
from contracts.execution import PromoteStageRequest, PromoteStageResult
from contracts.supervisor import DispatchResult
from kernel import AgentMessage

if TYPE_CHECKING:
    from contracts.operator import TypedIntent
    from kernel import GraphStore, MessageBus


VALID_STAGES = {"paper", "broker_shadow", "live_manual", "live_autopilot"}


def dispatch_intent(
    graph: GraphStore, intent: TypedIntent, *, bus: MessageBus | None = None
) -> DispatchResult:
    """Gate one intent and return a routing hint without executing it."""
    blocked, reason = is_hard_no(intent)
    if blocked:
        return rejected(intent.provenance.run_id, reason)
    spec = CAPABILITY_MATRIX[intent.family]
    if intent.family == "stage":
        return _dispatch_stage(intent, bus)
    if _needs_confirmation(intent):
        write_flag(
            graph,
            subject_ref=intent.provenance.run_id,
            severity="warn",
            reason="awaiting confirmation",
        )
        return rejected(
            intent.provenance.run_id,
            "confirmation required - resubmit with confirmed=true",
        )
    if intent.parameters.get("confirmed") == "true":
        resolve_flag(graph, intent.provenance.run_id, "warn")
    if not spec.available:
        return rejected(intent.provenance.run_id, not_available_reason(intent.family))
    if intent.family == "approve":
        subject_ref = intent.parameters.get("subject") or intent.parameters.get(
            "target", ""
        )
        resolve_flag_by_subject(graph, subject_ref)
    node = write_message(
        graph,
        run_id=intent.provenance.run_id,
        step_name=intent.family,
        status="dispatched",
    )
    return DispatchResult(
        accepted=True,
        routed_to=spec.routed_to,
        provenance=provenance(intent.provenance.run_id, "Message", node.key),
    )


def _needs_confirmation(intent: TypedIntent) -> bool:
    return intent.requires_confirmation and intent.parameters.get("confirmed") != "true"


def _dispatch_stage(intent: TypedIntent, bus: MessageBus | None) -> DispatchResult:
    if bus is None:
        return rejected(intent.provenance.run_id, "stage dispatch requires bus context")
    target = intent.parameters.get("stage") or intent.parameters.get("target", "")
    if target not in VALID_STAGES:
        return rejected(intent.provenance.run_id, f"invalid stage target: {target}")
    response = bus.request(
        AgentMessage(
            sender="supervisor",
            recipient="execution",
            message_type="request",
            capability="promote_stage",
            payload=PromoteStageRequest(
                target_stage=target,  # type: ignore[arg-type]
                reason=(f"operator stage request via {intent.provenance.source_agent}"),
                confirmed=intent.parameters.get("confirmed") == "true",
            ).model_dump(mode="json"),
        )
    )
    if response.message_type == "error":
        return rejected(
            intent.provenance.run_id,
            str(response.payload.get("message", "stage failed")),
        )
    result = PromoteStageResult.model_validate(response.payload)
    if not result.accepted:
        return rejected(intent.provenance.run_id, result.reason)
    return DispatchResult(
        accepted=True,
        routed_to="execution.promote_stage",
        provenance=result.provenance,
    )
