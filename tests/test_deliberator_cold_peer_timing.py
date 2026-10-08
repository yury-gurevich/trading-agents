"""Deliberator cold-peer timing tests.

Agent: deliberator
Role: prove served peers do not sleep through the manager reply deadline.
External I/O: none.
"""

from __future__ import annotations

import agents.deliberator.entrypoint as entrypoint
from agents.deliberator.settings import DeliberatorSettings
from kernel import (
    AzureServiceBusSettings,
    CollectingFaultSink,
    FakeLLMClient,
    InMemoryGraphStore,
)
from kernel.fault_graph import GraphFaultSink


def test_served_peer_uses_receive_wait_without_extra_idle_sleep(monkeypatch) -> None:
    """DLIB-IDM-04 / DLIB-DEP-02 / DLIB-PERF-02: B2 graph sink, no idle sleep."""
    seen: dict[str, object] = {}
    monkeypatch.setattr(entrypoint, "consumer_from_env", lambda _id, _graph: object())

    def fake_serve_loop(
        consumer: object, bus: object, *, poll_interval: int, sink: object
    ) -> None:
        seen["consumer"] = consumer
        seen["bus"] = bus
        seen["poll_interval"] = poll_interval
        seen["sink"] = sink

    monkeypatch.setattr(entrypoint, "serve_loop", fake_serve_loop)

    graph = InMemoryGraphStore()
    entrypoint.serve_peer(
        graph,
        DeliberatorSettings(role="proponent", instance_name="deliberator-proponent"),
        FakeLLMClient({}),
    )

    assert seen["poll_interval"] == entrypoint.PEER_SERVE_IDLE_SLEEP_SECONDS == 0
    assert AzureServiceBusSettings(_env_file=None).receive_timeout_seconds == 5.0
    assert DeliberatorSettings(role="manager").request_timeout_seconds > 5.0
    sink = seen["sink"]
    assert isinstance(sink, GraphFaultSink)
    assert sink.graph is graph
    assert isinstance(sink.inner, CollectingFaultSink)
