"""Execution broker-native stop graph-pull tests.

Agent: execution
Role: prove resting stop placement, cleanup, and stop-fill reconciliation.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

from agents.execution.broker import BrokerFill
from agents.execution.paper_broker import PaperBroker
from agents.execution.poll import execute_pm_node
from agents.execution.tests.broker_stop_helpers import (
    TrackingBroker,
    order_set,
    position,
    seed_pm_run,
    sell,
)
from agents.monitor.reconcile import reconcile_positions_from_latest_snapshot
from agents.monitor.settings import MonitorSettings
from contracts.broker_stops import active_broker_stop_refs
from contracts.common import Money
from contracts.positions import open_positions
from kernel import CollectingFaultSink, InMemoryGraphStore


def test_execute_pm_node_places_one_weighted_broker_stop_idempotently() -> None:
    graph = InMemoryGraphStore()
    broker = PaperBroker()
    sink = CollectingFaultSink()
    broker.submit("seed:AAPL", "AAPL", "buy", 4, Money(amount=Decimal("175.00")))
    position(graph, "a:AAPL", "AAPL", 1, opened_price_cents=10000)
    position(graph, "b:AAPL", "AAPL", 3, opened_price_cents=20000)
    ref = open_positions(graph)[0].position_ref
    node = seed_pm_run(graph, order_set("pm-stop"))

    execute_pm_node(node, graph=graph, broker=broker, sink=sink)
    execute_pm_node(node, graph=graph, broker=broker, sink=sink)

    stops = graph.list_nodes("BrokerStopOrder")
    fill = graph.get_node("Fill", f"stop:{ref}:AAPL")
    assert len(stops) == 1
    assert stops[0].props["position_ref"] == ref
    assert stops[0].props["stop_price_cents"] == 16625
    assert stops[0].props["broker_order_id"] == f"paper:stop:{ref}:AAPL"
    assert fill is not None
    assert fill.props["status"] == "pending"
    assert fill.props["quantity"] == 4
    assert fill.props["position_ref"] == ref
    assert fill.props["price_cents"] == 16625
    protected = graph.ancestors(stops[0], max_depth=1, edge_types={"PROTECTED_BY"})
    assert {node.key for node in protected} == {"a:AAPL", "b:AAPL"}
    assert active_broker_stop_refs(graph) == frozenset({ref})
    assert {fill.idempotency_key for fill in broker.fills()} == {
        "seed:AAPL",
        f"stop:{ref}:AAPL",
    }
    assert sink.faults == []


def test_execute_pm_node_skips_stop_for_ticker_sold_this_run() -> None:
    graph = InMemoryGraphStore()
    broker = PaperBroker()
    broker.submit("seed:AAPL", "AAPL", "buy", 4, Money(amount=Decimal("100.00")))
    position(graph, "held:AAPL", "AAPL", 4, opened_price_cents=10000)
    ref = open_positions(graph)[0].position_ref
    node = seed_pm_run(graph, order_set("pm-sell", sell("AAPL", 4, ref)))

    execute_pm_node(node, graph=graph, broker=broker)

    assert graph.list_nodes("BrokerStopOrder") == ()
    fill_keys = {fill.idempotency_key for fill in broker.fills()}
    assert f"exit:{ref}:AAPL:sell" in fill_keys
    assert f"stop:{ref}:AAPL" not in fill_keys


def test_execute_pm_node_cancels_stale_stop_once() -> None:
    graph = InMemoryGraphStore()
    broker = TrackingBroker()
    node = seed_pm_run(graph, order_set("pm-cancel"))
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

    execute_pm_node(node, graph=graph, broker=broker)
    execute_pm_node(node, graph=graph, broker=broker)

    stop = graph.get_node("BrokerStopOrder", "stop:old:AAPL")
    assert stop is not None
    assert "cancelled_at" in stop.props
    assert broker.cancelled == ["broker-stop-1"]


def test_stop_fill_refresh_books_pnl_then_monitor_reconciliation_closes() -> None:
    graph = InMemoryGraphStore()
    position(graph, "held:ABT", "ABT", 2, opened_price_cents=10000)
    ref = open_positions(graph)[0].position_ref
    placing_broker = PaperBroker()
    placing_broker.submit("seed:ABT", "ABT", "buy", 2, Money(amount=Decimal("100.00")))
    execute_pm_node(
        seed_pm_run(graph, order_set("pm-place")),
        graph=graph,
        broker=placing_broker,
    )
    key = f"stop:{ref}:ABT"
    broker = TrackingBroker(
        broker_fills=(
            BrokerFill(
                key,
                "ABT",
                "sell",
                2,
                Money(amount=Decimal("94.00")),
                f"paper:{key}",
                "filled",
            ),
        )
    )

    execute_pm_node(
        seed_pm_run(graph, order_set("pm-refresh")), graph=graph, broker=broker
    )
    assert open_positions(graph)
    reconcile_positions_from_latest_snapshot(graph, MonitorSettings())

    fill = graph.get_node("Fill", key)
    assert fill is not None
    assert fill.props["broker_status"] == "filled"
    assert fill.props["broker_price_cents"] == 9400
    assert fill.props["realized_pnl_cents"] == -1200
    assert open_positions(graph) == ()
    assert graph.list_nodes("CloseDecision") == ()
