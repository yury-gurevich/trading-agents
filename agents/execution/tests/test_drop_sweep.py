"""Drop-sweep tests for ADR-0018 same-session decisions.

Agent: execution
Role: prove stale orders are dropped while broker-native stops survive.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.drop_sweep import sweep_unfilled_orders
from agents.execution.run import run_submit
from agents.execution.settings import ExecutionSettings
from agents.execution.tests.broker_stop_helpers import TrackingBroker
from agents.execution.tests.drop_sweep_helpers import (
    SelectiveCancelBroker,
    TrackingSubmitBroker,
    broker_order,
    seed_fill_lineage,
    sell,
    stop_fact,
)
from agents.execution.tests.helpers import order_set
from kernel import CollectingFaultSink, GraphFaultSink, InMemoryGraphStore


def test_sweep_cancels_prior_run_order_and_records_drop() -> None:
    """EXEC-STA-03 / EXEC-OBS-02 / EXEC-FAIL-01: stale drop is visible."""
    graph = InMemoryGraphStore()
    key = "old-run:AAPL:buy"
    seed_fill_lineage(graph, "old-run", key, "AAPL")
    broker = TrackingBroker(broker_fills=(broker_order(key, "AAPL"),))
    sink = GraphFaultSink(graph, CollectingFaultSink())

    dropped = sweep_unfilled_orders(graph, broker, sink, run_id="new-run")

    fill = graph.get_node("Fill", key)
    execution = graph.get_node("ExecutionRun", "execution-submit-old-run")
    assert dropped == 1
    assert broker.cancelled == [f"broker:{key}"]
    assert fill is not None
    assert fill.props["broker_status"] == "canceled"
    assert fill.props["drop_reason"] == "unfilled at session end"
    assert execution is not None
    assert execution.props["dropped"] == 1
    assert "decided_price=100.00" in graph.list_nodes("Fault")[0].props["message"]
    assert graph.list_nodes("BrokerOrderStatus")


def test_sweep_leaves_current_and_filled_orders_alone() -> None:
    """EXEC-IDM-01 / EXEC-IDM-02: current-run and filled orders are not dropped."""
    graph = InMemoryGraphStore()
    stale = "old-run:OLD:buy"
    current = "new-run:NEW:buy"
    filled = "old-run:FILL:buy"
    seed_fill_lineage(graph, "old-run", stale, "OLD")
    seed_fill_lineage(graph, "new-run", current, "NEW")
    seed_fill_lineage(graph, "old-run", filled, "FILL")
    broker = TrackingBroker(
        broker_fills=(
            broker_order(stale, "OLD"),
            broker_order(current, "NEW"),
            broker_order(filled, "FILL", status="filled"),
        )
    )

    dropped = sweep_unfilled_orders(
        graph, broker, CollectingFaultSink(), run_id="new-run"
    )

    assert dropped == 1
    assert broker.cancelled == [f"broker:{stale}"]
    current_fill = graph.get_node("Fill", current)
    filled_fill = graph.get_node("Fill", filled)
    assert current_fill is not None
    assert filled_fill is not None
    assert current_fill.props.get("drop_reason") is None
    assert filled_fill.props.get("drop_reason") is None


def test_sweep_is_idempotent_for_same_run() -> None:
    """EXEC-IDM-01 / EXEC-STA-03: second sweep writes no duplicate drop."""
    graph = InMemoryGraphStore()
    key = "old-run:AAPL:buy"
    seed_fill_lineage(graph, "old-run", key, "AAPL")
    broker = TrackingBroker(broker_fills=(broker_order(key, "AAPL"),))
    sink = GraphFaultSink(graph, CollectingFaultSink())

    first = sweep_unfilled_orders(graph, broker, sink, run_id="new-run")
    second = sweep_unfilled_orders(graph, broker, sink, run_id="new-run")

    assert (first, second) == (1, 0)
    assert broker.cancelled == [f"broker:{key}"]
    assert len(graph.list_nodes("Fault")) == 1
    assert len(graph.list_nodes("BrokerOrderStatus")) == 1


def test_sweep_exempts_resting_stops_and_prefixless_stop() -> None:
    """EXEC-NEV-01 / EXEC-NEV-03: broker stops are risk instruments, not drops."""
    graph = InMemoryGraphStore()
    stale = "old-run:ENTRY:buy"
    seed_fill_lineage(graph, "old-run", stale, "ENTRY")
    stop_orders = tuple(
        broker_order(f"stop:ref-{idx}:S{idx}", f"S{idx}", order_type="stop")
        for idx in range(7)
    )
    prefixless = broker_order("custom-stop-client", "SAFE", order_type="stop")
    for order in (*stop_orders, prefixless):
        stop_fact(graph, order.idempotency_key, order.ticker, order.broker_order_id)
    broker = TrackingBroker(
        broker_fills=(*stop_orders, prefixless, broker_order(stale, "ENTRY"))
    )

    dropped = sweep_unfilled_orders(
        graph, broker, CollectingFaultSink(), run_id="new-run"
    )

    assert dropped == 1
    assert broker.cancelled == [f"broker:{stale}"]


def test_cancel_failure_is_contained_and_other_orders_continue() -> None:
    """EXEC-FAIL-01 / EXEC-FAIL-02: one cancel failure does not stop fan-out."""
    graph = InMemoryGraphStore()
    keys = ("old-run:AAA:buy", "old-run:BAD:buy", "old-run:CCC:buy")
    for key in keys:
        seed_fill_lineage(graph, "old-run", key, key.split(":")[1])
    broker = SelectiveCancelBroker(
        broker_fills=tuple(broker_order(key, key.split(":")[1]) for key in keys),
        fail_order_id=f"broker:{keys[1]}",
    )
    sink = GraphFaultSink(graph, CollectingFaultSink())

    dropped = sweep_unfilled_orders(graph, broker, sink, run_id="new-run")

    assert dropped == 2
    assert broker.cancelled == [f"broker:{keys[0]}", f"broker:{keys[2]}"]
    failed_fill = graph.get_node("Fill", keys[1])
    assert failed_fill is not None
    assert failed_fill.props.get("drop_reason") is None
    assert any(
        "cancel failed for BAD" in fault.props["message"]
        for fault in graph.list_nodes("Fault")
    )


def test_dropped_exit_key_can_be_redecided_tomorrow() -> None:
    """EXEC-IDM-01 / EXEC-NEV-03: cancelled exit key appends a fresh attempt."""
    graph = InMemoryGraphStore()
    old_key = "exit:ref:AMD:sell"
    graph.merge_node(
        "Fill",
        old_key,
        {
            "ticker": "AMD",
            "side": "sell",
            "quantity": 3,
            "price_cents": 10000,
            "price_currency": "USD",
            "broker_order_id": "broker:old",
            "status": "pending",
            "broker_status": "canceled",
            "drop_reason": "unfilled at session end",
            "broker_idempotency_key": old_key,
            "attempt_ordinal": 0,
        },
    )
    sell_order = sell("AMD", "ref")

    result = run_submit(
        graph,
        TrackingSubmitBroker(),
        CollectingFaultSink(),
        {},
        order_set(sell_order),
        settings=ExecutionSettings(),
    )

    assert result.submitted == 1
    assert result.rejected == 0
    replayed = graph.get_node("Fill", f"{old_key}#1")
    assert replayed is not None
    assert replayed.props["status"] == "filled"
