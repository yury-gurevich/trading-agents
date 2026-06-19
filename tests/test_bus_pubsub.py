"""Pub/sub fan-out tests for InProcessBus and CeleryBus.

Agent: kernel
Role: verify publish/subscribe deliver events to all registered handlers, in order,
      without crossing topics; silent on unknown topics.
External I/O: none.
"""

from __future__ import annotations

from kernel import CeleryBus, InProcessBus


# ── InProcessBus ─────────────────────────────────────────────────────────────


def test_in_process_subscribe_receives_published_event() -> None:
    bus = InProcessBus()
    received: list[dict[str, object]] = []
    bus.subscribe("my.topic", received.append)

    bus.publish("my.topic", {"key": "value"})

    assert received == [{"key": "value"}]


def test_in_process_fan_out_delivers_to_all_subscribers() -> None:
    bus = InProcessBus()
    r1: list[dict[str, object]] = []
    r2: list[dict[str, object]] = []
    bus.subscribe("my.topic", r1.append)
    bus.subscribe("my.topic", r2.append)

    bus.publish("my.topic", {"x": 1})

    assert r1 == [{"x": 1}]
    assert r2 == [{"x": 1}]


def test_in_process_publish_to_unknown_topic_is_silent() -> None:
    bus = InProcessBus()
    bus.publish("ghost.topic", {"x": 1})  # must not raise


def test_in_process_separate_topics_do_not_cross() -> None:
    bus = InProcessBus()
    r_a: list[dict[str, object]] = []
    r_b: list[dict[str, object]] = []
    bus.subscribe("topic.a", r_a.append)
    bus.subscribe("topic.b", r_b.append)

    bus.publish("topic.a", {"source": "a"})

    assert r_a == [{"source": "a"}]
    assert r_b == []


def test_in_process_multiple_publishes_arrive_in_order() -> None:
    bus = InProcessBus()
    received: list[int] = []
    bus.subscribe("seq", lambda e: received.append(e["n"]))

    for n in (1, 2, 3):
        bus.publish("seq", {"n": n})

    assert received == [1, 2, 3]


# ── CeleryBus (in-process fan-out; no broker needed) ─────────────────────────


def test_celery_bus_subscribe_receives_published_event() -> None:
    bus = CeleryBus()
    received: list[dict[str, object]] = []
    bus.subscribe("my.topic", received.append)

    bus.publish("my.topic", {"key": "value"})

    assert received == [{"key": "value"}]


def test_celery_bus_fan_out_delivers_to_all_subscribers() -> None:
    bus = CeleryBus()
    r1: list[dict[str, object]] = []
    r2: list[dict[str, object]] = []
    bus.subscribe("t", r1.append)
    bus.subscribe("t", r2.append)

    bus.publish("t", {"n": 1})

    assert r1 == [{"n": 1}]
    assert r2 == [{"n": 1}]


def test_celery_bus_publish_to_unknown_topic_is_silent() -> None:
    bus = CeleryBus()
    bus.publish("ghost.topic", {})  # must not raise
