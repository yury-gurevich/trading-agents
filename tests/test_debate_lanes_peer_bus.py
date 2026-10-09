"""The manager's supplied publisher and its unchanged default.

Agent: deliberator
Role: prove the D2 constructor seam uses the supplied bus.
External I/O: none.
"""

from __future__ import annotations

from tests.deliberator_correlated_peer_helpers import ReplyReceiver, turn_request

from agents.deliberator.servicebus_peer_client import ServiceBusPeerClient
from kernel import AzureServiceBusBus, AzureServiceBusSettings, InMemoryGraphStore
from kernel.bus import InProcessBus


class RecordingBus(InProcessBus):
    def __init__(self):
        super().__init__()
        self.events = []

    def __bool__(self):
        return False

    def publish(self, topic, event):
        self.events.append((topic, event))


def test_manager_publisher_can_be_supplied():
    """DL-279 A7 / DLIB-DEP-02: ready events go to the supplied publisher."""
    graph = InMemoryGraphStore()
    bus = RecordingBus()
    settings = AzureServiceBusSettings(
        connection_string=None, connection_strings_json=None
    )
    receiver = ReplyReceiver(graph, [], fresh_ref="lanes-reply")
    peer = ServiceBusPeerClient(
        graph,
        sender="deliberator-manager",
        settings=settings,
        timeout_seconds=1.0,
        reply_receiver=receiver,
        bus=bus,
    )
    reply = peer.debate_turn("deliberator-proponent", turn_request())
    assert reply.request_id == turn_request().request_id
    ((topic, event),) = bus.events
    assert topic == "deliberator-proponent.requests"
    assert event["topic"] == topic
    assert event["run_id"] == reply.request_id
    request = graph.get_node("AgentMessage", event["ref"])
    assert request.props["payload"]["request_id"] == reply.request_id
    assert peer._bus is bus

    default = ServiceBusPeerClient(
        graph, sender="deliberator-manager", settings=settings
    )
    assert isinstance(default._bus, AzureServiceBusBus)
