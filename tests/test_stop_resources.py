"""Stop-time graph and request-consumer closure proofs.

Agent: kernel
Role: verify wrapper delegation and idempotent Service Bus resource release.
External I/O: none; Azure resources are synthetic.
"""

from __future__ import annotations

from tests.bus_azure_receiver_helpers import FakeReceiver, raw_ready, request

from kernel import (
    AzureServiceBusBus,
    AzureServiceBusRequestConsumer,
    AzureServiceBusSettings,
    InMemoryGraphStore,
)
from kernel.graph_guarded import GuardedGraphStore
from kernel.graph_vocabulary import Vocabulary


def test_a13_guarded_graph_closes_its_wrapped_store() -> None:
    """MST-TRG-03: a guarded connection closes once; a store without close is valid."""

    class Graph(InMemoryGraphStore):
        closes = 0

        def close(self):
            self.closes += 1

    graph = Graph()
    vocabulary = Vocabulary.from_mapping({})
    GuardedGraphStore(graph, vocabulary).close()
    assert graph.closes == 1
    GuardedGraphStore(InMemoryGraphStore(), vocabulary).close()


def test_a14_consumer_closes_receiver_then_client_and_can_poll_again(
    monkeypatch,
) -> None:
    """MST-TRG-03: close clears both resources, is idempotent and permits reuse."""
    calls: list[str] = []

    class Receiver(FakeReceiver):
        def close(self):
            calls.append("receiver")

    class Client:
        def close(self):
            calls.append("client")

    local = AzureServiceBusSettings(
        _env_file=None, connection_string=None, connection_strings_json=None
    )
    bus = AzureServiceBusBus(settings=local)
    graph = InMemoryGraphStore()
    consumer = AzureServiceBusRequestConsumer(
        bus,
        graph,
        topic="echo.requests",
        subscription_name="echo",
        settings=local,
        receiver=Receiver([]),
    )
    consumer._client = Client()
    consumer.close()
    consumer.close()
    assert calls == ["receiver", "client"]
    assert consumer._receiver is None
    assert consumer._client is None
    assert consumer.poll() == []
    message = request()
    later = FakeReceiver([raw_ready(graph, bus, message)])
    monkeypatch.setattr(consumer, "_open_receiver", lambda: later)
    consumer._settings = AzureServiceBusSettings(
        _env_file=None, connection_string="local-fixture", connection_strings_json=None
    )
    assert consumer.poll() == [message]
    assert later.completed
