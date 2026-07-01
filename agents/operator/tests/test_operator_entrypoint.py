"""Serve the operator over serve_loop — S98 (build_served_bus + serve_once).

Agent: operator
Role: verify serve_loop dispatches the operator's interpret capability.
External I/O: none.
"""

from __future__ import annotations

from agents.operator.entrypoint import build_served_bus
from kernel import InMemoryGraphStore
from kernel.envelope import AgentMessage
from kernel.serve_loop import LocalRequestConsumer, serve_once


def _interpret_request(sender: str) -> AgentMessage:
    return AgentMessage(
        sender=sender,
        recipient="operator",
        message_type="request",
        capability="interpret",
        payload={"text": "status please", "actor": "owner", "channel": "dashboard"},
    )


def test_serve_loop_dispatches_interpret_and_returns_command_result() -> None:
    graph = InMemoryGraphStore()
    bus = build_served_bus(graph)
    consumer = LocalRequestConsumer([_interpret_request("owner")])

    count = serve_once(consumer, bus)

    assert count == 1
    (reply,) = consumer.replies
    assert reply.message_type == "response"
    # default FakeLLMClient resolves to a status intent — the handler ran end-to-end.
    assert reply.payload["outcome"] == "intent"
