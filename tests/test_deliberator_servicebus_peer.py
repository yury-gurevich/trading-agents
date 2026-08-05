"""Service Bus deliberator peer-client tests.

Agent: deliberator
Role: cover claim-checked Service Bus peer reply handling without live Azure I/O.
External I/O: none.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from agents.deliberator.peer_client import ServiceBusPeerClient
from contracts.deliberator import (
    DebateProposition,
    DebateTurnRecord,
    DebateTurnReply,
    DebateTurnRequest,
)
from kernel import AgentMessage, AzureServiceBusSettings, InMemoryGraphStore
from kernel.serve_transport import request_topic


def _offline_servicebus_settings() -> AzureServiceBusSettings:
    return AzureServiceBusSettings(
        connection_string=None,
        connection_strings_json=None,
    )


def _require_dotenv_file() -> None:
    if not Path(".env").is_file():
        pytest.skip("A1 proof requires .env present; CI has no local secrets file")
    assert Path(".env").is_file()


def _turn_request(role: str = "defender") -> DebateTurnRequest:
    return DebateTurnRequest(
        request_id="turn-1",
        proposition=DebateProposition(decision="buy AAPL", context="ctx"),
        role=role,  # type: ignore[arg-type]
        round_number=1,
    )


def test_servicebus_peer_tests_inject_offline_settings(monkeypatch) -> None:
    """A1 / DEP-BUS-04: offline settings override loaded Service Bus env."""
    _require_dotenv_file()
    monkeypatch.setenv(
        "SERVICEBUS_CONNECTION_STRING",
        "Endpoint=sb://example/;SharedAccessKeyName=fake;SharedAccessKey=fake",
    )

    settings = _offline_servicebus_settings()

    assert (
        settings.connection_string_for_topic(request_topic("deliberator-proponent"))
        is None
    )


def test_servicebus_peer_client_reads_claim_checked_reply(monkeypatch) -> None:
    """A2 / DLIB-DEP-02: offline settings keep peer requests in-process."""
    graph = InMemoryGraphStore()
    client = ServiceBusPeerClient(
        graph,
        sender="deliberator-manager",
        settings=_offline_servicebus_settings(),
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
    """A2 / DLIB-NEV-06: an error reply stays loud on the offline path."""
    graph = InMemoryGraphStore()
    client = ServiceBusPeerClient(
        graph,
        sender="deliberator-manager",
        settings=_offline_servicebus_settings(),
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
