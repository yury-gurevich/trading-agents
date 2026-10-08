"""An in-process competing-receiver transport for production debate code.

Agent: tooling
Role: supply the bus and receivers, including active and dead-letter counts.
External I/O: none; connection strings are explicitly absent.
"""

from __future__ import annotations

import json
import threading
import time
from collections import Counter, defaultdict, deque
from typing import TYPE_CHECKING, Any

from scripts.debate_lanes_model import MANAGER, SUBSCRIPTION

from agents.deliberator.servicebus_peer_client import ServiceBusPeerClient
from kernel import AzureServiceBusRequestConsumer, AzureServiceBusSettings
from kernel.serve_transport import request_topic

if TYPE_CHECKING:
    from kernel import FaultSink, InMemoryGraphStore


class Raw:
    """The raw receiver body consumed by the production ready-event reader."""

    def __init__(self, body: str) -> None:
        self.body = body
        self.delivery_count = 1


class MemoryBroker:
    """Deliver a queued event to exactly one receiver, up to its batch count."""

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._queues: dict[str, deque[Raw]] = defaultdict(deque)
        self.dead: Counter[str] = Counter()

    def publish(self, topic: str, event: dict[str, Any]) -> None:
        with self._cond:
            self._queues[topic].append(Raw(json.dumps(event)))
            self._cond.notify_all()

    def take(self, topic: str, count: int, wait: float) -> list[Raw]:
        deadline = time.monotonic() + wait
        with self._cond:
            queue = self._queues[topic]
            while not queue:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return []
                self._cond.wait(remaining)
            return [queue.popleft() for _ in range(min(count, len(queue)))]

    def left(self, topic: str) -> int:
        with self._cond:
            return len(self._queues[topic])


class MemoryReceiver:
    """Expose the receiver slice the production request consumer and inbox use."""

    def __init__(self, broker: MemoryBroker, topic: str) -> None:
        self._broker, self._topic = broker, topic

    def receive_messages(
        self, *, max_message_count: int, max_wait_time: float
    ) -> list[Raw]:
        return self._broker.take(self._topic, max_message_count, max_wait_time)

    def complete_message(self, message: Raw) -> None:
        del message

    def abandon_message(self, message: Raw) -> None:
        self._broker.publish(self._topic, json.loads(message.body))

    def dead_letter_message(self, message: Raw, *, reason: str) -> None:
        del message, reason
        with self._broker._cond:
            self._broker.dead[self._topic] += 1


class MemoryTransport:
    """Use the production request consumer and peer client over memory ports."""

    name = "memory"

    def __init__(self, requests_a_pass: int | None = None) -> None:
        self.broker = MemoryBroker()
        self.proponent, self.opponent = "lanes-proponent", "lanes-opponent"
        overrides = (
            {} if requests_a_pass is None else {"receive_max_messages": requests_a_pass}
        )
        self.sb = AzureServiceBusSettings(
            _env_file=None,
            connection_string=None,
            connection_strings_json=None,
            receive_timeout_seconds=0.2,
            **overrides,
        )
        self.reply_topic = f"{MANAGER}{self.sb.reply_topic_suffix}"

    def consumer(
        self, graph: InMemoryGraphStore, identity: str
    ) -> AzureServiceBusRequestConsumer:
        topic = request_topic(identity)
        return AzureServiceBusRequestConsumer(
            self.broker,
            graph,
            topic=topic,
            subscription_name=SUBSCRIPTION,
            settings=self.sb,
            receiver=MemoryReceiver(self.broker, topic),
        )

    def peer_client(
        self, graph: InMemoryGraphStore, wait: float, sink: FaultSink
    ) -> ServiceBusPeerClient:
        return ServiceBusPeerClient(
            graph,
            sender=MANAGER,
            settings=self.sb,
            timeout_seconds=wait,
            reply_receiver=MemoryReceiver(self.broker, self.reply_topic),
            sink=sink,
            bus=self.broker,
        )

    def counts(self) -> dict[str, dict[str, int]]:
        topics = (
            request_topic(self.proponent),
            request_topic(self.opponent),
            self.reply_topic,
        )
        return {
            t: {"active": self.broker.left(t), "dead": self.broker.dead[t]}
            for t in topics
        }

    def close(self) -> list[str]:
        return []
