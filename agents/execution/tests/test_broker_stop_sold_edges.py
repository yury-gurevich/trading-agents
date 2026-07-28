"""Broker-stop sold-ticker edge tests.

Agent: execution
Role: preserve the full-exit skip while reporting real exposure.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.broker_stops import place_broker_stops
from agents.execution.tests.broker_stop_helpers import (
    PendingStopBroker,
    order_set,
    sell,
)
from contracts.positions import open_positions
from kernel import CollectingFaultSink, InMemoryGraphStore, Node


def test_bad_stop_threshold_is_not_faulted_when_position_is_sold() -> None:
    """EXEC-NEV-03 / EXEC-OBS-02: full exits suppress stop-placement faults."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    broker = PendingStopBroker()
    _position(graph, "held:AAPL", "AAPL", True)
    ref = open_positions(graph)[0].position_ref

    place_broker_stops(
        graph,
        broker,
        sink,
        order_set("pm-run", sell("AAPL", 1, ref)),
        _snapshot(graph, ({"ticker": "AAPL", "quantity": 1},)),
        fallback_stop_pct=0.05,
    )

    assert broker.submitted == []
    assert sink.faults == []


def _position(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    quantity: object,
) -> None:
    graph.merge_node(
        "Position",
        key,
        {
            "run_id": "seed",
            "ticker": ticker,
            "quantity": quantity,
            "target_pct": 0.10,
            "horizon_days": 10,
            "opened_at": "2026-07-20",
            "opened_price_cents": 10000,
            "status": "open",
            "stop_pct": 0.05,
        },
    )


def _snapshot(graph: InMemoryGraphStore, holdings: tuple[object, ...]) -> Node:
    return graph.merge_node(
        "BrokerPositionSnapshot",
        "snapshot",
        {"status": "fresh", "holdings": holdings},
    )
