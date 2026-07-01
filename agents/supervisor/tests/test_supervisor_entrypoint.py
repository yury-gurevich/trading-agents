"""Serve the supervisor over serve_loop — S98 (build_served_bus + serve_once).

Agent: supervisor
Role: verify serve_loop dispatches the supervisor's flag_for_human capability.
External I/O: none.
"""

from __future__ import annotations

from agents.supervisor.entrypoint import build_served_bus
from kernel import InMemoryGraphStore
from kernel.envelope import AgentMessage
from kernel.serve_loop import LocalRequestConsumer, serve_once


def _flag_request(sender: str) -> AgentMessage:
    return AgentMessage(
        sender=sender,
        recipient="supervisor",
        message_type="request",
        capability="flag_for_human",
        payload={
            "subject_ref": "AAPL:run-1",
            "severity": "warn",
            "reason": "test flag",
        },
    )


def test_serve_loop_dispatches_flag_for_human_and_writes_flag() -> None:
    graph = InMemoryGraphStore()
    bus = build_served_bus(graph)
    consumer = LocalRequestConsumer([_flag_request("operator")])

    count = serve_once(consumer, bus)

    assert count == 1
    (reply,) = consumer.replies
    assert reply.message_type == "response"
    assert reply.payload["accepted"] is True
    # the served handler ran for real — a Flag node was written to the graph.
    assert graph.list_nodes("Flag")
