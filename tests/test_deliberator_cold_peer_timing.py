"""Deliberator cold-peer timing tests.

Agent: deliberator
Role: prove served peers do not sleep through the manager reply deadline.
External I/O: none.
"""

from __future__ import annotations

import agents.deliberator.entrypoint as entrypoint
from agents.deliberator.settings import DeliberatorSettings
from kernel import AzureServiceBusSettings, FakeLLMClient, InMemoryGraphStore


def test_served_peer_uses_receive_wait_without_extra_idle_sleep(monkeypatch) -> None:
    """DLIB-DEP-02 / DLIB-PERF-02: cold peers poll inside the manager deadline."""
    seen: dict[str, object] = {}
    monkeypatch.setattr(entrypoint, "consumer_from_env", lambda _id, _graph: object())

    def fake_serve_loop(consumer: object, bus: object, *, poll_interval: int) -> None:
        seen["consumer"] = consumer
        seen["bus"] = bus
        seen["poll_interval"] = poll_interval

    monkeypatch.setattr(entrypoint, "serve_loop", fake_serve_loop)

    entrypoint.serve_peer(
        InMemoryGraphStore(),
        DeliberatorSettings(role="proponent", instance_name="deliberator-proponent"),
        FakeLLMClient({}),
    )

    assert seen["poll_interval"] == entrypoint.PEER_SERVE_IDLE_SLEEP_SECONDS == 0
    assert AzureServiceBusSettings(_env_file=None).receive_timeout_seconds == 5.0
    assert DeliberatorSettings(role="manager").request_timeout_seconds > 5.0
