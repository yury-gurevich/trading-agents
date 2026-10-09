"""Disposable live topics for the debate lanes command.

Agent: tooling
Role: refuse fleet names, compare fleet subscription counts and delete created topics.
External I/O: Azure Service Bus only when LiveTransport is constructed explicitly.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from scripts.debate_lanes_model import MANAGER, SUBSCRIPTION

from agents.deliberator.servicebus_peer_client import ServiceBusPeerClient
from kernel import AzureServiceBusBus, AzureServiceBusSettings
from kernel.serve_transport import request_topic

if TYPE_CHECKING:
    from kernel import AzureServiceBusRequestConsumer, FaultSink, InMemoryGraphStore

PRODUCTION_TOPICS = frozenset(
    {
        "deliberator-manager.reply",
        "deliberator-proponent.requests",
        "deliberator-opponent.requests",
    }
)


def guard_topic_names(run_id: str, topics: tuple[str, ...]) -> None:
    """Refuse a fleet topic or a name not containing this nonempty run id."""
    if not run_id or any(t in PRODUCTION_TOPICS or run_id not in t for t in topics):
        raise ValueError("refused non-disposable Service Bus topic name")


def topic_names(run_id: str) -> tuple[str, str, str]:
    """Name three topics using the manager's identity and a disposable suffix."""
    topics = (
        request_topic(f"{run_id}-proponent"),
        request_topic(f"{run_id}-opponent"),
        f"{MANAGER}.{run_id}.reply",
    )
    guard_topic_names(run_id, topics)
    return topics


class LiveTransport:
    """Create and remove three topics per configuration, with lazy SDK imports."""

    name = "live"

    def __init__(self, requests_a_pass: int | None = None) -> None:
        connection_string = AzureServiceBusSettings(_env_file=None).connection_string
        if not connection_string:
            raise ValueError("SERVICEBUS_CONNECTION_STRING is required for live")
        run_id = f"lanes-{uuid.uuid4().hex[:10]}"
        self.topics = topic_names(run_id)
        self.proponent, self.opponent = f"{run_id}-proponent", f"{run_id}-opponent"
        self.reply_topic = self.topics[2]
        overrides = (
            {} if requests_a_pass is None else {"receive_max_messages": requests_a_pass}
        )
        self.sb = AzureServiceBusSettings(
            _env_file=None,
            connection_string=connection_string,
            connection_strings_json=None,
            receive_timeout_seconds=2.0,
            reply_topic_suffix=f".{run_id}.reply",
            **overrides,
        )
        from azure.servicebus.management import ServiceBusAdministrationClient

        self._admin = ServiceBusAdministrationClient.from_connection_string(
            connection_string
        )
        self._created: list[str] = []
        self.production_unchanged = True
        self.production_before = self._production()
        self.production_after: dict[str, Any] = {}
        try:
            for topic in self.topics:
                self._admin.create_topic(topic)
                self._created.append(topic)
                self._admin.create_subscription(topic, SUBSCRIPTION)
        except Exception:
            self.close()
            raise

    def consumer(
        self, graph: InMemoryGraphStore, identity: str
    ) -> AzureServiceBusRequestConsumer:
        return AzureServiceBusBus(settings=self.sb).request_consumer(
            graph, topic=request_topic(identity)
        )

    def peer_client(
        self, graph: InMemoryGraphStore, wait: float, sink: FaultSink
    ) -> ServiceBusPeerClient:
        return ServiceBusPeerClient(
            graph, sender=MANAGER, settings=self.sb, timeout_seconds=wait, sink=sink
        )

    def counts(self) -> dict[str, dict[str, int]]:
        out = {}
        for topic in self.topics:
            runtime = self._admin.get_subscription_runtime_properties(
                topic, SUBSCRIPTION
            )
            out[topic] = {
                "active": runtime.active_message_count,
                "dead": runtime.dead_letter_message_count,
            }
        return out

    def _production(self) -> dict[str, Any]:
        out = {}
        for topic in sorted(PRODUCTION_TOPICS):
            try:
                runtime = self._admin.get_subscription_runtime_properties(
                    topic, SUBSCRIPTION
                )
                out[topic] = {
                    "active": runtime.active_message_count,
                    "dead": runtime.dead_letter_message_count,
                }
            except Exception as exc:
                out[topic] = {"unreadable": type(exc).__name__}
        return out

    def close(self) -> list[str]:
        result = []
        try:
            self.production_after = self._production()
            self.production_unchanged = all(
                before == self.production_after[topic]
                for topic, before in self.production_before.items()
                if "unreadable" not in before
                and "unreadable" not in self.production_after[topic]
            )
            for topic in self._created:
                try:
                    self._admin.delete_topic(topic)
                    result.append(f"{topic}: deleted")
                except Exception as exc:
                    result.append(f"{topic}: NOT deleted ({type(exc).__name__})")
        finally:
            self._admin.close()
        return result
