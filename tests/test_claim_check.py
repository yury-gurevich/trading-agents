"""Claim-check produce + consume tests.

Agent: kernel
Role: verify that claim_check_write stores the artifact in the graph and publishes
      only a small ref-event to the bus; claim_check_read resolves the event back to
      the node; missing ref raises RuntimeError.
External I/O: none.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from kernel import (
    InMemoryGraphStore,
    InProcessBus,
    ReadyEvent,
    claim_check_read,
    claim_check_write,
)


def _wire() -> tuple[InProcessBus, InMemoryGraphStore]:
    return InProcessBus(), InMemoryGraphStore()


# ── claim_check_write ─────────────────────────────────────────────────────────


def test_write_stores_node_in_graph() -> None:
    bus, graph = _wire()
    claim_check_write(
        bus, graph, topic="data.ohlcv.ready", label="OHLCVData", ref="ohlcv:AAPL:r1",
        props={"ticker": "AAPL", "bars": 10},
    )
    node = graph.get_node("OHLCVData", "ohlcv:AAPL:r1")
    assert node is not None
    assert node.props["ticker"] == "AAPL"


def test_write_publishes_ready_event_to_topic() -> None:
    bus, graph = _wire()
    received: list[dict[str, object]] = []
    bus.subscribe("data.ohlcv.ready", received.append)

    claim_check_write(
        bus, graph, topic="data.ohlcv.ready", label="OHLCVData", ref="ohlcv:AAPL:r1",
        props={"ticker": "AAPL"},
    )

    assert len(received) == 1
    assert received[0]["ref"] == "ohlcv:AAPL:r1"
    assert received[0]["label"] == "OHLCVData"
    assert received[0]["topic"] == "data.ohlcv.ready"


def test_write_event_does_not_carry_raw_props() -> None:
    bus, graph = _wire()
    received: list[dict[str, object]] = []
    bus.subscribe("data.ohlcv.ready", received.append)

    claim_check_write(
        bus, graph, topic="data.ohlcv.ready", label="OHLCVData", ref="ohlcv:AAPL:r1",
        props={"ticker": "AAPL", "secret_data": [1, 2, 3]},
    )

    event = received[0]
    assert "secret_data" not in event
    assert "ticker" not in event
    assert set(event.keys()) == {"topic", "label", "ref", "run_id"}


def test_write_propagates_run_id_in_event() -> None:
    bus, graph = _wire()
    received: list[dict[str, object]] = []
    bus.subscribe("t", received.append)

    claim_check_write(
        bus, graph, topic="t", label="L", ref="r", props={}, run_id="run-42",
    )

    assert received[0]["run_id"] == "run-42"


def test_write_returns_ready_event() -> None:
    bus, graph = _wire()
    event = claim_check_write(
        bus, graph, topic="t", label="L", ref="my-ref", props={"x": 1},
    )
    assert isinstance(event, ReadyEvent)
    assert event.ref == "my-ref"
    assert event.label == "L"
    assert event.run_id is None


# ── claim_check_read ──────────────────────────────────────────────────────────


def test_read_resolves_event_to_graph_node() -> None:
    bus, graph = _wire()
    received: list[dict[str, object]] = []
    bus.subscribe("data.ohlcv.ready", received.append)
    claim_check_write(
        bus, graph, topic="data.ohlcv.ready", label="OHLCVData", ref="ohlcv:AAPL:r1",
        props={"ticker": "AAPL", "bars": 10},
    )

    node = claim_check_read(graph, received[0])

    assert node.label == "OHLCVData"
    assert node.key == "ohlcv:AAPL:r1"
    assert node.props["bars"] == 10


def test_read_raises_on_missing_ref() -> None:
    _, graph = _wire()
    event = {"topic": "t", "label": "Missing", "ref": "no-such-ref", "run_id": None}

    with pytest.raises(RuntimeError, match="no 'Missing' node for ref 'no-such-ref'"):
        claim_check_read(graph, event)


# ── full round-trip ───────────────────────────────────────────────────────────


def test_produce_consume_round_trip() -> None:
    bus, graph = _wire()
    consumed_nodes = []

    def on_ready(event: dict[str, object]) -> None:
        consumed_nodes.append(claim_check_read(graph, event))

    bus.subscribe("data.news.ready", on_ready)

    claim_check_write(
        bus, graph, topic="data.news.ready", label="NewsData", ref="news:MSFT:r2",
        props={"ticker": "MSFT", "articles": 5}, run_id="run-1",
    )

    assert len(consumed_nodes) == 1
    assert consumed_nodes[0].props["articles"] == 5
    assert consumed_nodes[0].key == "news:MSFT:r2"


# ── ReadyEvent immutability ───────────────────────────────────────────────────


def test_ready_event_is_frozen() -> None:
    event = ReadyEvent(topic="t", label="L", ref="r")
    with pytest.raises((ValidationError, TypeError)):
        event.ref = "changed"  # type: ignore[misc]
