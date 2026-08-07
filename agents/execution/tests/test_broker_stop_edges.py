"""Execution broker-stop edge-path coverage tests.

Agent: execution
Role: prove defensive broker-stop branches under the graph-pull path.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.broker_stop_actions import cancel_stop, place_stop
from agents.execution.broker_stops import place_broker_stops
from agents.execution.paper_broker import PaperBroker
from agents.execution.tests.broker_stop_helpers import (
    CancelRaisesBroker,
    PendingStopBroker,
    RuntimeStopBroker,
    VanishingPositionGraph,
    order_set,
    position,
    stop_threshold,
)
from contracts.broker_stops import BrokerStopOrder
from contracts.positions import open_positions
from kernel import CollectingFaultSink, InMemoryGraphStore, Node


def test_place_stop_records_rejected_fill_without_stop_order() -> None:
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()

    place_stop(
        graph,
        PaperBroker(reject_tickers={"AAPL"}),
        sink,
        stop_threshold("AAPL", "missing-ref", 2),
        "stop:missing-ref:AAPL",
    )

    fill = graph.get_node("Fill", "stop:missing-ref:AAPL")
    assert fill is not None
    assert fill.props["status"] == "rejected"
    assert fill.props["reason"] == "paper_broker_rejected"
    assert graph.list_nodes("BrokerStopOrder") == ()
    assert sink.faults[-1].error_type == "BrokerRejectedError"


def test_place_stop_records_broker_outage_as_rejected_fill() -> None:
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()

    place_stop(
        graph,
        RuntimeStopBroker(),
        sink,
        stop_threshold("AAPL", "missing-ref", 2),
        "stop:missing-ref:AAPL",
    )

    fill = graph.get_node("Fill", "stop:missing-ref:AAPL")
    assert fill is not None
    assert fill.props["status"] == "rejected"
    assert fill.props["reason"] == "broker offline"
    assert graph.list_nodes("BrokerStopOrder") == ()
    assert sink.faults[-1].error_type == "RuntimeError"


def test_cancel_stop_failure_leaves_stop_active() -> None:
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    graph.merge_node(
        "BrokerStopOrder",
        "stop:old:AAPL",
        {
            "ticker": "AAPL",
            "position_ref": "old",
            "stop_price_cents": 9500,
            "broker_order_id": "broker-stop-1",
            "placed_at": "2026-07-25T00:00:00+00:00",
        },
    )

    cancel_stop(
        graph,
        CancelRaisesBroker(),
        sink,
        BrokerStopOrder(
            key="stop:old:AAPL",
            ticker="AAPL",
            position_ref="old",
            stop_price_cents=9500,
            broker_order_id="broker-stop-1",
            placed_at="2026-07-25T00:00:00+00:00",
        ),
    )

    stop = graph.get_node("BrokerStopOrder", "stop:old:AAPL")
    assert stop is not None
    assert "cancelled_at" not in stop.props
    assert sink.faults[-1].error_type == "RuntimeError"


def test_place_stop_without_active_basis_records_order_without_edges() -> None:
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()

    place_stop(
        graph,
        PendingStopBroker(),
        sink,
        stop_threshold("AAPL", "missing-ref", 2),
        "stop:missing-ref:AAPL",
    )

    stop = graph.get_node("BrokerStopOrder", "stop:missing-ref:AAPL")
    assert stop is not None
    assert list(graph.ancestors(stop, max_depth=1, edge_types={"PROTECTED_BY"})) == []
    assert sink.faults == []


def test_place_stop_tolerates_position_that_vanishes_before_linking() -> None:
    graph = VanishingPositionGraph()
    position(graph, "held:AAPL", "AAPL", 2, opened_price_cents=10000)
    ref = open_positions(graph)[0].position_ref
    graph.position_reads = 0
    graph.hide_after_position_reads = 2

    place_stop(
        graph,
        PendingStopBroker(),
        CollectingFaultSink(),
        stop_threshold("AAPL", ref, 2),
        f"stop:{ref}:AAPL",
    )

    stop = graph.get_node("BrokerStopOrder", f"stop:{ref}:AAPL")
    assert stop is not None
    assert list(graph.ancestors(stop, max_depth=1, edge_types={"PROTECTED_BY"})) == []


def test_place_broker_stops_skips_missing_snapshot_and_active_key() -> None:
    graph = InMemoryGraphStore()
    broker = PendingStopBroker()
    position(graph, "held:AAPL", "AAPL", 2, opened_price_cents=10000)

    place_broker_stops(graph, broker, CollectingFaultSink(), order_set("pm-stop"), None)
    assert broker.submitted == []

    ref = open_positions(graph)[0].position_ref
    graph.merge_node(
        "BrokerStopOrder",
        f"stop:{ref}:AAPL",
        {
            "ticker": "AAPL",
            "position_ref": ref,
            "stop_price_cents": 9500,
            "broker_order_id": "broker-stop-1",
            "placed_at": "2026-07-25T00:00:00+00:00",
        },
    )
    snapshot = _snapshot(graph, ({"ticker": "AAPL", "quantity": 2},))

    place_broker_stops(
        graph, broker, CollectingFaultSink(), order_set("pm-stop"), snapshot
    )

    assert broker.submitted == []


def test_place_broker_stops_ignores_malformed_snapshot_holdings() -> None:
    graph = InMemoryGraphStore()
    broker = PendingStopBroker()
    position(graph, "held:AAPL", "AAPL", 2, opened_price_cents=10000)
    ref = open_positions(graph)[0].position_ref
    snapshot = _snapshot(
        graph,
        (
            "not-a-holding",
            {"ticker": "", "quantity": 2},
            {"ticker": "AAPL", "quantity": 0},
            {"ticker": "AAPL", "quantity": 2},
        ),
    )

    place_broker_stops(
        graph, broker, CollectingFaultSink(), order_set("pm-stop"), snapshot
    )

    assert broker.submitted == [f"stop:{ref}:AAPL"]


def _snapshot(graph: InMemoryGraphStore, holdings: tuple[object, ...]) -> Node:
    return graph.merge_node(
        "BrokerPositionSnapshot",
        "snapshot",
        {"status": "fresh", "holdings": holdings},
    )
