"""Execution broker-stop coverage for fills not yet adopted by monitor.

Agent: execution
Role: prove newly filled positions are protected before monitor writes Position.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from agents.execution.broker import BrokerFill, BrokerRejectedError
from agents.execution.broker_stops import place_broker_stops
from agents.execution.tests.broker_stop_helpers import PendingStopBroker, order_set
from contracts.position_refs import position_ref_for_keys
from kernel import AgentFault, CollectingFaultSink, InMemoryGraphStore, Node

if TYPE_CHECKING:
    from contracts.common import Money


def test_filled_entry_without_position_is_protected_from_fill_lineage() -> None:
    """EXEC-OBS-03 / MON-IDN-02: protect filled entries without writing Position."""
    graph = InMemoryGraphStore()
    broker = PendingStopBroker()
    sink = CollectingFaultSink()
    _seed_filled_entry(graph, "entry-run", "AAPL", quantity=3, price_cents=12500)

    place_broker_stops(
        graph,
        broker,
        sink,
        order_set("pm-next"),
        _snapshot(graph, ({"ticker": "AAPL", "quantity": 3},)),
        fallback_stop_pct=0.05,
    )

    (stop,) = graph.list_nodes("BrokerStopOrder")
    fill = graph.get_node("Fill", stop.key)
    assert stop.props["ticker"] == "AAPL"
    assert stop.props["position_ref"] == position_ref_for_keys(("entry-run:AAPL",))
    assert stop.props["stop_price_cents"] == 11875
    assert fill is not None
    assert fill.props["status"] == "pending"
    assert graph.list_nodes("Position") == ()
    assert broker.submitted == [stop.key]
    assert _unprotected_faults(sink) == []


def test_filled_entry_stop_wash_trade_rejection_stays_loud() -> None:
    """EXEC-OBS-02 / EXEC-OBS-03: 403 stop rejection leaves fault evidence."""
    graph = InMemoryGraphStore()
    broker = _WashTradeRejectingBroker()
    sink = CollectingFaultSink()
    _seed_filled_entry(graph, "entry-run", "MO", quantity=15, price_cents=4600)

    place_broker_stops(
        graph,
        broker,
        sink,
        order_set("pm-next"),
        _snapshot(graph, ({"ticker": "MO", "quantity": 15},)),
        fallback_stop_pct=0.05,
    )

    (fill,) = [
        node for node in graph.list_nodes("Fill") if node.key.startswith("stop:")
    ]
    assert graph.list_nodes("BrokerStopOrder") == ()
    assert fill.props["status"] == "rejected"
    assert "potential wash trade" in str(fill.props["reason"])
    assert "opposite side market/limit order exists" in str(fill.props["reason"])
    unprotected = _unprotected_faults(sink)
    assert len(unprotected) == 1
    assert "potential wash trade" in str(unprotected[0].context["reason"])


class _WashTradeRejectingBroker(PendingStopBroker):
    def submit_stop(
        self,
        idempotency_key: str,
        ticker: str,
        side: Literal["buy", "sell"],
        quantity: int,
        stop_price: Money,
        tif: str = "gtc",
    ) -> BrokerFill:
        self.submitted.append(idempotency_key)
        reason = (
            "HTTP 403 potential wash trade detected. use complex orders; "
            "opposite side market/limit order exists"
        )
        raise BrokerRejectedError(
            BrokerFill(
                idempotency_key=idempotency_key,
                ticker=ticker,
                side=side,
                quantity=quantity,
                price=stop_price,
                broker_order_id=f"rejected:{idempotency_key}",
                status="rejected",
                reason=reason,
                time_in_force=tif,
            )
        )


def _seed_filled_entry(
    graph: InMemoryGraphStore,
    run_id: str,
    ticker: str,
    *,
    quantity: int,
    price_cents: int,
) -> None:
    run = graph.merge_node("PMRun", run_id, {"approved_count": 1})
    order = graph.merge_node(
        "OrderIntent",
        f"{run_id}:{ticker}",
        {
            "ticker": ticker,
            "action": "buy",
            "quantity": quantity,
            "stop_pct": 0.05,
            "target_pct": 0.10,
        },
    )
    fill = graph.merge_node(
        "Fill",
        f"{run_id}:{ticker}:buy",
        {
            "ticker": ticker,
            "side": "buy",
            "quantity": quantity,
            "price_cents": price_cents,
            "price_currency": "USD",
            "broker_order_id": f"paper:{run_id}:{ticker}:buy",
            "status": "filled",
            "reason": None,
            "source_run_id": run_id,
        },
    )
    graph.add_edge(order, run, "EMITTED_BY")
    graph.add_edge(fill, order, "EXECUTES")


def _snapshot(graph: InMemoryGraphStore, holdings: tuple[object, ...]) -> Node:
    return graph.merge_node(
        "BrokerPositionSnapshot",
        "snapshot",
        {"status": "fresh", "holdings": holdings},
    )


def _unprotected_faults(sink: CollectingFaultSink) -> list[AgentFault]:
    return [fault for fault in sink.faults if fault.error_type == "UnprotectedPosition"]
