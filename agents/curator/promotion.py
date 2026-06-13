"""Predictor promotion orchestration.

Agent: curator
Role: run the evidence-gate -> operator-approval -> audit promotion flow.
External I/O: MessageBus call to supervisor.flag_for_human.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from agents.curator.domain.registry import check_promotion_evidence, is_promoted
from agents.curator.store import write_promotion
from contracts.common import Explanation, Provenance
from contracts.curator import PromotionResult, PromotionStatus
from contracts.supervisor import FlagRequest
from kernel import AgentMessage, CollectingFaultSink
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from agents.curator.settings import CuratorSettings
    from kernel import GraphStore, MessageBus, Node

# matches the flag the supervisor raises for predictor approval
_SEVERITY: Literal["info"] = "info"


def run_promotion(
    *,
    graph: GraphStore,
    bus: MessageBus,
    settings: CuratorSettings,
    predictor_id: str,
) -> PromotionResult:
    """Evidence-gate, then raise-flag-or-promote depending on approval state."""
    predictor = graph.get_node("Predictor", predictor_id)
    if predictor is None:
        return _result(predictor_id, "not_found", "advisory", "unknown predictor")
    evidence = _evidence_text(predictor)
    if is_promoted(graph, predictor_id):
        return _result(
            predictor_id,
            "already_promoted",
            "load_bearing",
            "already promoted",
            evidence,
        )
    ok, reason = check_promotion_evidence(predictor, settings)
    if not ok:
        return _result(predictor_id, "rejected", "advisory", reason, evidence)
    return _gate_on_approval(graph, bus, predictor, predictor_id, evidence)


def _gate_on_approval(
    graph: GraphStore,
    bus: MessageBus,
    predictor: Node,
    predictor_id: str,
    evidence: str,
) -> PromotionResult:
    subject = f"predictor:{predictor_id}"
    resolution = graph.get_node(
        "FlagResolution", f"resolution:flag:{subject}:{_SEVERITY}"
    )
    if resolution is not None:
        write_promotion(graph, predictor=predictor, approval_ref=resolution.key)
        return _result(
            predictor_id,
            "promoted",
            "load_bearing",
            "evidence gate passed; operator approved",
            evidence,
        )
    if graph.get_node("Flag", f"flag:{subject}:{_SEVERITY}") is None:
        _raise_flag(bus, predictor_id, subject)
    return _result(
        predictor_id,
        "pending_approval",
        "advisory",
        "operator approval required",
        evidence,
    )


def _raise_flag(bus: MessageBus, predictor_id: str, subject: str) -> None:
    # Flag is supervisor-owned (single-writer); the curator requests it over the
    # bus, exactly as the researcher does, and never imports agents.supervisor.
    with fault_boundary(
        CollectingFaultSink(),
        agent="curator",
        module="agents.curator.promotion",
        capability="promote_predictor.flag",
        reraise=False,
    ):
        bus.request(
            AgentMessage(
                sender="curator",
                recipient="supervisor",
                message_type="request",
                capability="flag_for_human",
                payload=FlagRequest(
                    subject_ref=subject,
                    severity=_SEVERITY,
                    reason=(
                        f"predictor {predictor_id} passed evidence gate; "
                        "awaiting approval"
                    ),
                ).model_dump(mode="json"),
            )
        )


def _evidence_text(predictor: Node) -> str:
    accuracy = float(predictor.props.get("accuracy", 0.0))
    sample_size = int(predictor.props.get("sample_size", 0))
    return f"accuracy {accuracy:.2f} over {sample_size} examples"


def _result(
    predictor_id: str,
    status: PromotionStatus,
    state: str,
    reason: str,
    evidence: str = "no frozen evidence",
) -> PromotionResult:
    return PromotionResult(
        predictor_id=predictor_id,
        status=status,
        state=state,  # type: ignore[arg-type]
        reason=reason,
        explanation=Explanation(summary=f"{status}: {reason} ({evidence})"),
        provenance=Provenance(
            run_id=f"promotion:{predictor_id}",
            source_agent="curator",
            graph_node_id=f"Predictor:{predictor_id}",
        ),
    )
