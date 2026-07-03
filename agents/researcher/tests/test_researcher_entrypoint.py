"""Researcher served-entrypoint tests.

Agent: researcher
Role: verify request-triggered serving queues proposals without applying changes.
External I/O: none.
"""

from __future__ import annotations

from agents.researcher.entrypoint import build_served_bus
from agents.researcher.tests.helpers import seed_snapshots
from contracts.researcher import ParameterChangeProposal, ResearchRequest
from kernel import AgentMessage, InMemoryGraphStore
from kernel.serve_loop import LocalRequestConsumer, serve_once


def _propose_message() -> AgentMessage:
    return AgentMessage(
        sender="test",
        recipient="researcher",
        message_type="request",
        capability="propose",
        payload=ResearchRequest().model_dump(mode="json"),
    )


def test_served_propose_is_request_triggered_and_review_only() -> None:
    """RES-TRG-03 / RES-NEV-01: served propose writes review artifacts only."""
    graph = InMemoryGraphStore()
    seed_snapshots(graph, confidence=0.35)
    bus = build_served_bus(graph)
    consumer = LocalRequestConsumer([_propose_message()])

    served = serve_once(consumer, bus)

    assert served == 1
    assert len(consumer.replies) == 1
    proposal = ParameterChangeProposal.model_validate(consumer.replies[0].payload)
    assert proposal.changes
    assert len(graph.list_nodes("Experiment")) == 1
    assert len(graph.list_nodes("ParamChange")) == 1
    assert graph.list_nodes("ParameterSetting") == ()
    assert graph.list_nodes("StrategyParameter") == ()
    assert graph.list_nodes("ActiveParameter") == ()
