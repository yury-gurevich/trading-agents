"""Partial-fill sweep, settlement and protection proofs.

Agent: execution
Role: prove the filled part is retained, reported once and protected at its size.
External I/O: none.
"""

from agents.execution.drop_sweep import sweep_unfilled_orders
from agents.execution.filled_entry_stops import filled_entry_stop_thresholds
from agents.execution.reconciliation_store import refresh_pending_fills
from agents.execution.tests.broker_stop_helpers import TrackingBroker
from agents.execution.tests.partial_fill_helpers import (
    DECIDED_STOP,
    adopt_unh,
    mapped_unh,
    new_book,
    stored_fill,
)
from contracts.stop_width import decided_stop_pct


def test_the_sweep_drops_no_part_of_a_partly_filled_order() -> None:
    """EXEC-OUT-07: an ended partial order creates no drop evidence or fault."""
    graph, sink = new_book()
    broker = TrackingBroker(broker_fills=(mapped_unh(),))
    dropped = sweep_unfilled_orders(graph, broker, sink, run_id="next-run")
    assert dropped == 0
    assert broker.cancelled == []
    assert "drop_reason" not in stored_fill(graph).props
    assert graph.list_nodes("BrokerOrderStatus") == ()
    assert graph.list_nodes("Fault") == ()
    assert sink.faults == []


def test_an_ended_order_that_filled_nothing_is_still_dropped() -> None:
    """EXEC-OUT-07: zero execution stays a drop with normalized broker status."""
    graph, sink = new_book()
    fills = (mapped_unh(filled_qty="0"),)
    broker = TrackingBroker(broker_fills=fills)
    dropped = sweep_unfilled_orders(graph, broker, sink, run_id="next-run")
    refresh_pending_fills(graph, fills, sink)
    assert dropped == 1
    assert stored_fill(graph).props["drop_reason"] == "unfilled at session end"
    assert stored_fill(graph).props["broker_status"] == "rejected"
    assert {n.props["status"] for n in graph.list_nodes("BrokerOrderStatus")} == {
        "expired",
        "rejected",
    }
    assert [f.error_type for f in sink.faults] == ["DroppedDecision"]


def test_the_refresh_settles_the_filled_part_and_tells_the_rest_once() -> None:
    """EXEC-OUT-07 / EXEC-TYP-04 / EXEC-STA-05: settlement warns once."""
    graph, sink = new_book()
    fills = (mapped_unh(),)
    refresh_pending_fills(graph, fills, sink)
    first = dict(stored_fill(graph).props)
    refresh_pending_fills(graph, fills, sink)
    assert stored_fill(graph).props == first
    assert first["broker_status"] == "filled"
    assert first["broker_filled_quantity"] == 1
    assert first["broker_price_cents"] == 40111
    assert first["quantity"] == 2
    statuses = graph.list_nodes("BrokerOrderStatus")
    assert len(statuses) == 1
    assert statuses[0].props["quantity"] == 2
    assert statuses[0].props["filled_quantity"] == 1
    assert len(sink.faults) == 1
    fault = sink.faults[0]
    assert fault.error_type == "UnfilledRemainder"
    assert fault.severity == "warning"
    assert fault.message.startswith("filled 1 of 2 UNH side=buy;")
    assert "(expired)" in fault.message


def test_a_whole_fill_writes_its_quantity_and_tells_nothing() -> None:
    """EXEC-TYP-04: full execution writes its size without a remainder warning."""
    graph, sink = new_book()
    refresh_pending_fills(graph, (mapped_unh(status="filled", filled_qty="2"),), sink)
    assert stored_fill(graph).props["broker_status"] == "filled"
    assert stored_fill(graph).props["broker_filled_quantity"] == 2
    assert sink.faults == []


def test_an_ended_order_with_nothing_filled_writes_no_filled_quantity() -> None:
    """EXEC-OUT-07 / EXEC-TYP-04: rejection invents no executed size or warning."""
    graph, sink = new_book()
    refresh_pending_fills(graph, (mapped_unh(filled_qty="0"),), sink)
    assert stored_fill(graph).props["broker_status"] == "rejected"
    assert "broker_filled_quantity" not in stored_fill(graph).props
    assert sink.faults == []


def test_the_adopted_share_takes_the_decided_stop() -> None:
    """EXEC-OBS-06: refresh restores the adopted share's exact PM stop lineage."""
    graph, sink = new_book()
    position = adopt_unh(graph)
    before = decided_stop_pct(graph, position)
    assert before == (0.05, "fallback")
    refresh_pending_fills(graph, (mapped_unh(),), sink)
    after = decided_stop_pct(graph, position)
    assert after == (DECIDED_STOP, "lineage")


def test_the_entry_stop_covers_only_the_shares_the_broker_filled() -> None:
    """EXEC-OBS-06 / EXEC-TYP-04: the stop covers one share at the decided width."""
    graph, sink = new_book()
    refresh_pending_fills(graph, (mapped_unh(),), sink)
    plans = filled_entry_stop_thresholds(
        graph,
        broker_quantities={"UNH": 1},
        blocked_tickers=frozenset(),
        fallback_stop_pct=0.05,
    )
    assert len(plans) == 1
    threshold = plans[0].threshold
    assert threshold.quantity == 1
    assert threshold.opened_price_cents == 40111
    assert threshold.stop_pct == DECIDED_STOP
