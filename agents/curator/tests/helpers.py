"""Curator test helpers.

Agent: curator
Role: seed TradeNarrative lineage fixtures and build dataset request messages.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from agents.curator import CuratorAgent
from contracts.common import Provenance
from contracts.curator import (
    DatasetRequest,
    PromoteRequest,
    PromotionResult,
    TrainRequest,
)
from contracts.supervisor import DispatchResult, FlagRequest
from kernel import AgentMessage, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from collections.abc import Callable


def seed_narratives(
    graph: InMemoryGraphStore, count: int, *, trigger: str | None = "target"
) -> None:
    """Seed ``count`` TradeNarrative nodes plus Position/CloseDecision lineage."""
    for index in range(count):
        position_id = f"run-{index}:TICK{index}"
        position = graph.merge_node(
            "Position",
            position_id,
            {"run_id": f"run-{index}", "ticker": f"TICK{index}"},
        )
        narrative = graph.merge_node(
            "TradeNarrative",
            f"narrative:{position_id}",
            {
                "run_id": f"run-{index}",
                "position_id": position_id,
                "summary": f"story {index}",
            },
        )
        graph.add_edge(narrative, position, "NARRATES")
        if trigger is not None:
            close = graph.merge_node(
                "CloseDecision",
                f"monitor-{index}:{position_id}:close",
                {"position_id": position_id, "trigger": trigger},
            )
            graph.add_edge(close, position, "CLOSES")


def build_dataset_message(purpose: str = "exit-timing") -> AgentMessage:
    """Build a build_dataset request message for the curator."""
    return _message("build_dataset", purpose)


def describe_corpus_message(purpose: str = "exit-timing") -> AgentMessage:
    """Build a describe_corpus request message for the curator."""
    return _message("describe_corpus", purpose)


def train_predictor_message(
    purpose: str = "exit-timing",
    *,
    version: int | None = None,
    target: str = "exit_trigger",
) -> AgentMessage:
    """Build a train_predictor request message for the curator."""
    return AgentMessage(
        sender="test",
        recipient="curator",
        message_type="request",
        capability="train_predictor",
        payload=TrainRequest(
            purpose=purpose, version=version, target=target
        ).model_dump(mode="json"),
    )


def _message(capability: str, purpose: str) -> AgentMessage:
    return AgentMessage(
        sender="test",
        recipient="curator",
        message_type="request",
        capability=capability,
        payload=DatasetRequest(purpose=purpose).model_dump(mode="json"),
    )


def bind_curator_with_supervisor(graph: InMemoryGraphStore) -> InProcessBus:
    """Bind curator with a local fake supervisor flag_for_human handler.

    Mirrors agents/researcher/tests/helpers.py: the supervisor is the single
    Flag writer, so the test stands in a handler with the supervisor key formula
    rather than importing the supervisor agent (agents are islands).
    """
    bus = InProcessBus()
    bus.register("supervisor", "flag_for_human", _flag_handler(graph))
    CuratorAgent(bus, graph=graph).bind()
    return bus


def promote(bus: InProcessBus, predictor_id: str) -> PromotionResult:
    """Request curator.promote_predictor on a bound test bus."""
    response = bus.request(
        AgentMessage(
            sender="test",
            recipient="curator",
            message_type="request",
            capability="promote_predictor",
            payload=PromoteRequest(predictor_id=predictor_id).model_dump(mode="json"),
        )
    )
    return PromotionResult.model_validate(response.payload)


def approve_flag(graph: InMemoryGraphStore, predictor_id: str) -> None:
    """Append a FlagResolution for a predictor flag (operator-approval stand-in).

    Replicates agents/supervisor/store.py _resolution_key / resolve_flag: key
    ``resolution:flag:{subject}:info`` plus a RESOLVES edge to the Flag.
    """
    subject = f"predictor:{predictor_id}"
    flag = graph.get_node("Flag", f"flag:{subject}:info")
    assert flag is not None
    resolution = graph.merge_node(
        "FlagResolution",
        f"resolution:flag:{subject}:info",
        {"subject_ref": subject, "severity": "info"},
    )
    graph.add_edge(resolution, flag, "RESOLVES")


def _flag_handler(
    graph: InMemoryGraphStore,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def handle(payload: dict[str, Any]) -> dict[str, Any]:
        flag = FlagRequest.model_validate(payload)
        node = graph.merge_node(
            "Flag",
            f"flag:{flag.subject_ref}:{flag.severity}",
            {
                "subject_ref": flag.subject_ref,
                "severity": flag.severity,
                "reason": flag.reason,
                "created_at": datetime.now(tz=UTC).isoformat(),
            },
        )
        return DispatchResult(
            accepted=True,
            provenance=Provenance(
                run_id=flag.subject_ref,
                source_agent="supervisor",
                graph_node_id=f"Flag:{node.key}",
            ),
        ).model_dump(mode="json")

    return handle
