"""Researcher test helpers.

Agent: researcher
Role: provide local bus wiring and Snapshot fixtures for researcher tests.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agents.researcher import ResearcherAgent
from contracts.common import Provenance
from contracts.researcher import ParameterChangeProposal, ResearchRequest
from contracts.supervisor import DispatchResult, FlagRequest
from kernel import AgentMessage, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from collections.abc import Callable


def bound_bus(graph: InMemoryGraphStore) -> InProcessBus:
    """Bind researcher with a local fake supervisor flag handler."""
    bus = InProcessBus()
    bus.register("supervisor", "flag_for_human", _flag_handler(graph))
    ResearcherAgent(bus, graph=graph).bind()
    return bus


def propose(bus: InProcessBus) -> ParameterChangeProposal:
    """Request researcher.propose on a bound test bus."""
    response = request(bus, "propose")
    return ParameterChangeProposal.model_validate(response.payload)


def evidence_summary(bus: InProcessBus) -> str:
    """Request researcher.evidence on a bound test bus."""
    response = request(bus, "evidence")
    return str(response.payload["summary"])


def request(bus: InProcessBus, capability: str) -> AgentMessage:
    """Send one researcher request with the default research payload."""
    return bus.request(
        AgentMessage(
            sender="test",
            recipient="researcher",
            message_type="request",
            capability=capability,
            payload=ResearchRequest().model_dump(mode="json"),
        )
    )


def seed_snapshots(graph: InMemoryGraphStore, *, confidence: float) -> None:
    """Seed six Snapshot nodes with stable P7 evidence metrics."""
    for index in range(6):
        graph.merge_node(
            "Snapshot",
            f"snapshot:run-{index}",
            {
                "run_id": f"run-{index}",
                "metrics": {
                    "portfolio": {"approval_rate": 0.80},
                    "signal": {
                        "avg_confidence": confidence,
                        "rejection_count": 1.0,
                    },
                },
            },
        )


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
