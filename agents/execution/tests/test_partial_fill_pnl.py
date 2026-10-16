"""Realized PnL for the executed part of an ended sell.

Agent: execution
Role: prove partial sell arithmetic uses shares sold rather than shares ordered.
External I/O: none.
"""

from decimal import Decimal

from agents.execution.alpaca_orders import fill_from_order
from agents.execution.reconciliation_store import refresh_pending_fills
from agents.execution.tests.broker_stop_helpers import position
from agents.execution.tests.partial_fill_helpers import unh_order
from contracts.common import Money
from contracts.positions import open_positions
from kernel import CollectingFaultSink, InMemoryGraphStore


def test_a_partly_filled_sell_realizes_pnl_on_the_shares_it_sold() -> None:
    """EXEC-TYP-04 / EXEC-OUT-07: four sold shares earn 540 cents, rest warned."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    position(graph, "held:UNH", "UNH", 10, opened_price_cents=10000)
    ref = open_positions(graph)[0].position_ref
    key = "pm-run-sell:UNH:sell"
    graph.merge_node(
        "Fill",
        key,
        {
            "ticker": "UNH",
            "side": "sell",
            "quantity": 10,
            "status": "pending",
            "price_cents": 10000,
            "position_ref": ref,
            "broker_order_id": "sell-unh",
        },
    )
    order = unh_order(
        id="sell-unh",
        client_order_id=key,
        side="sell",
        qty="10",
        filled_qty="4",
        filled_avg_price="101.35",
    )
    fill = fill_from_order(order, key, Money(amount=Decimal("100.00")))
    refresh_pending_fills(graph, (fill,), sink)
    stored = graph.get_node("Fill", key)
    assert stored is not None
    assert stored.props["realized_pnl_cents"] == 540
    assert stored.props["broker_filled_quantity"] == 4
    assert stored.props["quantity"] == 10
    assert [f.error_type for f in sink.faults] == ["UnfilledRemainder"]
