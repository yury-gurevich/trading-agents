"""Resting-stop settlement for positions this run exits.

Agent: execution
Role: free an exited position's reserved shares by cancelling its own resting stop
      before submission, and keep a failed exit's unprotected position loud.
External I/O: injected Broker and GraphStore backends.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.broker_stop_actions import cancel_stop
from agents.execution.broker_stops import place_broker_stops, reconcile_broker_stops
from contracts.broker_stops import active_broker_stop_orders
from kernel import AgentFault

if TYPE_CHECKING:
    from agents.execution.broker import Broker
    from contracts.execution import ExecutionResult
    from contracts.portfolio_manager import OrderIntentSet
    from kernel import FaultSink, GraphStore, Node


def settle_stops(
    graph: GraphStore,
    broker: Broker,
    sink: FaultSink,
    order_set: OrderIntentSet,
    snapshot: Node | None,
    *,
    fallback_stop_pct: float,
) -> frozenset[str]:
    """Settle every resting stop before submission; return the tickers freed.

    Order matters: stale stops are reconciled, exited positions are freed, and only
    then are stops placed for the positions that survive the run.
    """
    reconcile_broker_stops(graph, broker, sink)
    freed = cancel_stops_for_exits(graph, broker, sink, order_set)
    place_broker_stops(
        graph, broker, sink, order_set, snapshot, fallback_stop_pct=fallback_stop_pct
    )
    return freed


def cancel_stops_for_exits(
    graph: GraphStore,
    broker: Broker,
    sink: FaultSink,
    order_set: OrderIntentSet,
) -> frozenset[str]:
    """Cancel the resting stop of every position this run exits (DL-95).

    A broker reserves a position's shares against its own open sell stop, so an exit
    submitted while that stop rests has no shares left to sell. The portfolio manager
    only ever approves full exits, so a sold ticker's stop always protects a position
    going to zero on this run -- ADR-0015 section 3 is not weakened.

    Only tickers whose fact actually flipped to cancelled are returned: a cancel that
    failed leaves the stop resting, so that position is still protected.
    """
    sold = {item.ticker for item in order_set.approved if item.action == "sell"}
    if not sold:
        return frozenset()
    targets = tuple(
        order for order in active_broker_stop_orders(graph) if order.ticker in sold
    )
    for order in targets:
        cancel_stop(graph, broker, sink, order)
    still_active = {order.ticker for order in active_broker_stop_orders(graph)}
    return frozenset(
        order.ticker for order in targets if order.ticker not in still_active
    )


def report_unprotected_exits(
    sink: FaultSink, result: ExecutionResult, freed: frozenset[str]
) -> None:
    """Fault for every freed position whose exit the broker rejected (EXEC-OBS-03).

    Its shares are still held and its stop is gone, so the position ends the run
    unprotected. Only a rejected sell is reported: a ticker with no fill at all was
    skipped as an already-completed exit and is no longer held.
    """
    if not freed:
        return
    for fill in result.fills:
        if fill.side != "sell" or fill.status != "rejected":
            continue
        if fill.ticker not in freed:
            continue
        _record_unprotected_exit(sink, fill.ticker, fill.quantity)


def _record_unprotected_exit(sink: FaultSink, ticker: str, quantity: int) -> None:
    reason = "exit rejected after its resting stop was cancelled"
    sink.submit(
        AgentFault(
            source_agent="execution",
            source_module="agents.execution.exit_stops",
            capability="report_unprotected_exits",
            severity="error",
            error_type="UnprotectedPosition",
            message=f"unprotected held position {ticker} qty={quantity}: {reason}",
            context={"ticker": ticker, "quantity": quantity, "reason": reason},
        )
    )
