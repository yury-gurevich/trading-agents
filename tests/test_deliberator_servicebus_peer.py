"""Service Bus deliberator peer-client tests.

Agent: deliberator
Role: cover claim-checked Service Bus peer reply handling without live Azure I/O.
External I/O: none.
"""

from __future__ import annotations

import uuid

import pytest

from agents.deliberator.peer_client import ServiceBusPeerClient
from contracts.deliberator import (
    DebateProposition,
    DebateTurnRecord,
    DebateTurnReply,
    DebateTurnRequest,
)
from kernel import AgentMessage, AzureServiceBusSettings, InMemoryGraphStore


def _turn_request(role: str = "defender") -> DebateTurnRequest:
    return DebateTurnRequest(
        request_id="turn-1",
        proposition=DebateProposition(decision="buy AAPL", context="ctx"),
        role=role,  # type: ignore[arg-type]
        round_number=1,
    )


def test_servicebus_peer_client_reads_claim_checked_reply(monkeypatch) -> None:
    graph = InMemoryGraphStore()
    client = ServiceBusPeerClient(
        graph,
        sender="deliberator-manager",
        settings=AzureServiceBusSettings(),
    )
    reply = AgentMessage(
        sender="deliberator-proponent",
        recipient="deliberator-manager",
        message_type="response",
        capability="debate_turn",
        payload=DebateTurnReply(
            request_id="turn-1",
            turn=DebateTurnRecord(role="defender", round=1, text="ok"),
        ).model_dump(mode="json"),
        correlation_id=uuid.uuid4(),
    )
    graph.merge_node("AgentMessage", "reply-ok", reply.model_dump(mode="json"))
    monkeypatch.setattr(
        client,
        "_read_ready_event",
        lambda: {"topic": "t", "label": "AgentMessage", "ref": "reply-ok"},
    )

    result = client.debate_turn("deliberator-proponent", _turn_request())

    assert result.turn.text == "ok"


def test_servicebus_peer_client_raises_on_error_reply(monkeypatch) -> None:
    graph = InMemoryGraphStore()
    client = ServiceBusPeerClient(
        graph,
        sender="deliberator-manager",
        settings=AzureServiceBusSettings(),
    )
    reply = AgentMessage(
        sender="deliberator-proponent",
        recipient="deliberator-manager",
        message_type="error",
        capability="debate_turn",
        payload={"message": "peer unavailable"},
        correlation_id=uuid.uuid4(),
    )
    graph.merge_node("AgentMessage", "reply-error", reply.model_dump(mode="json"))
    monkeypatch.setattr(
        client,
        "_read_ready_event",
        lambda: {"topic": "t", "label": "AgentMessage", "ref": "reply-error"},
    )

    with pytest.raises(RuntimeError, match="peer unavailable"):
        client.debate_turn("deliberator-proponent", _turn_request())
