"""Stage promotion flow for the execution agent.

Agent: execution
Role: coordinate stage eligibility, review flags, and transition writes.
External I/O: MessageBus request to supervisor.flag_for_human.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.domain.stage_gate import (
    check_promotion_allowed,
    collect_stage_evidence,
    is_valid_demotion,
    is_valid_promotion,
)
from agents.execution.store import current_stage_from_graph, write_stage_transition
from contracts.common import Provenance
from contracts.execution import PromoteStageResult
from contracts.supervisor import FlagRequest
from kernel import AgentMessage

if TYPE_CHECKING:
    from agents.execution.settings import ExecutionSettings
    from contracts.execution import ExecutionStage, PromoteStageRequest
    from kernel import GraphStore, MessageBus, Node


def promote_stage(
    graph: GraphStore,
    bus: MessageBus,
    settings: ExecutionSettings,
    request: PromoteStageRequest,
) -> PromoteStageResult:
    """Apply the stage transition gate and return the operator-facing result."""
    current = current_stage_from_graph(graph, settings.stage)
    target = request.target_stage
    if is_valid_demotion(current, target):
        return _transition(graph, current, target, request.reason, "demotion applied")
    if not is_valid_promotion(current, target):
        return _result(
            False, current, current, f"invalid transition {current}->{target}"
        )
    subject_ref = f"stage_promote:{target}"
    if request.confirmed and _flag_resolved(graph, subject_ref):
        return _transition(
            graph, current, target, request.reason, "promotion confirmed and applied"
        )
    allowed, reason = check_promotion_allowed(collect_stage_evidence(graph), settings)
    if not allowed:
        return _result(False, current, current, reason)
    _request_confirmation(bus, current, target, subject_ref)
    return _result(
        False,
        current,
        current,
        f"confirmation required - approve stage:promote:{target} to proceed",
    )


def _transition(
    graph: GraphStore,
    from_stage: ExecutionStage,
    to_stage: ExecutionStage,
    reason: str,
    result_reason: str,
) -> PromoteStageResult:
    node = write_stage_transition(
        graph, from_stage=from_stage, to_stage=to_stage, reason=reason
    )
    return _result(True, from_stage, to_stage, result_reason, node)


def _request_confirmation(
    bus: MessageBus, current: ExecutionStage, target: ExecutionStage, subject_ref: str
) -> None:
    bus.request(
        AgentMessage(
            sender="execution",
            recipient="supervisor",
            message_type="request",
            capability="flag_for_human",
            payload=FlagRequest(
                subject_ref=subject_ref,
                severity="info",
                reason=f"Promote execution stage {current}->{target}",
            ).model_dump(mode="json"),
        )
    )


def _flag_resolved(graph: GraphStore, subject_ref: str) -> bool:
    # Mirrors agents/supervisor/store.py: resolution:{flag:<subject_ref>:<severity>}.
    key = f"resolution:flag:{subject_ref}:info"
    return graph.get_node("FlagResolution", key) is not None


def _result(
    accepted: bool,
    previous_stage: ExecutionStage,
    current_stage: ExecutionStage,
    reason: str,
    node: Node | None = None,
) -> PromoteStageResult:
    return PromoteStageResult(
        accepted=accepted,
        previous_stage=previous_stage,
        current_stage=current_stage,
        reason=reason,
        provenance=Provenance(
            run_id="stage-promotion",
            source_agent="execution",
            graph_node_id=None if node is None else f"{node.label}:{node.key}",
        ),
    )
