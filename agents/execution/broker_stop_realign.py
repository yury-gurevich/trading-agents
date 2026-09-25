"""Move a live broker stop that rests away from its decided price (S230).

Agent: execution
Role: replace a mismatched resting stop in place, never cancel-then-place (DL-223).
External I/O: injected Broker and GraphStore backends.

EXEC-OBS-06: the stop resting at the broker is the one the PM decided. The
replacement is Alpaca's atomic replace, so a held position is never without a
live stop. Every refused or failed replace is a warning fault; the old stop stays.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import TYPE_CHECKING

from agents.execution.broker_stop_writes import (
    STOP_FILL_EDGE,
    link_positions,
    mark_replaced,
    write_stop_fill,
    write_stop_order,
)
from contracts.broker_stops import active_broker_stop_orders, free_broker_stop_order_key
from contracts.stop_rule import stop_price_cents
from kernel import AgentFault

if TYPE_CHECKING:
    from collections.abc import Sequence

    from agents.execution.broker import Broker
    from agents.execution.broker_stop_types import BrokerStopThresholdPlan
    from contracts.broker_stops import BrokerStopOrder
    from kernel import FaultSink, GraphStore, Node

# Both prices are integer cents from contracts/stop_rule.py: the same opened price
# and the same decided stop_pct give the same cents every run, so a one-cent
# difference is a real move and not rounding flutter (DL-223, proven by A11/A12).
REPLACE_TOLERANCE_CENTS = 1
# Alpaca replaces only a `new` order; it refuses an `accepted` one with 422
# (measured on paper 2026-09-25). A stop placed after the close is `accepted`.
REPLACEABLE_ORDER_STATUS = "new"
_CENTS = Decimal("100")
_DOLLARS = Decimal("0.01")

_Target = tuple["BrokerStopThresholdPlan", "BrokerStopOrder", int]


def realign_broker_stops(
    graph: GraphStore,
    broker: Broker,
    sink: FaultSink,
    plans: Sequence[BrokerStopThresholdPlan],
    snapshot: Node | None,
) -> None:
    """Replace each protected position's live stop resting off its decided price."""
    targets = _mismatched(graph, plans)
    if not targets:
        return
    statuses = _order_statuses(broker, sink, targets)
    if statuses is None:
        return
    values = _market_values(snapshot)
    for plan, stop, decided in targets:
        status = statuses.get(stop.broker_order_id)
        value = values.get(plan.threshold.ticker, 0)
        _realign(graph, broker, sink, (plan, stop, decided), status, value)


def _mismatched(
    graph: GraphStore, plans: Sequence[BrokerStopThresholdPlan]
) -> list[_Target]:
    live = {order.position_ref: order for order in active_broker_stop_orders(graph)}
    targets: list[_Target] = []
    for plan in plans:
        threshold = plan.threshold
        decided = stop_price_cents(threshold.opened_price_cents, threshold.stop_pct)
        stop = live.get(threshold.position_ref)
        if stop is not None and abs(stop.stop_price_cents - decided) >= (
            REPLACE_TOLERANCE_CENTS
        ):
            targets.append((plan, stop, decided))
    return targets


def _order_statuses(
    broker: Broker, sink: FaultSink, targets: list[_Target]
) -> dict[str, str | None] | None:
    try:
        orders = broker.fills()
    except Exception as exc:
        for target in targets:
            _record(
                sink, "StopReplaceFailed", target, f"broker orders unreadable: {exc}"
            )
        return None
    return {order.broker_order_id: order.order_status for order in orders}


def _market_values(snapshot: Node | None) -> dict[str, int]:
    holdings = () if snapshot is None else snapshot.props.get("holdings", ())
    return {
        str(item.get("ticker", "")): int(item.get("market_value_cents", 0))
        for item in holdings
        if isinstance(item, Mapping)
    }


def _realign(
    graph: GraphStore,
    broker: Broker,
    sink: FaultSink,
    target: _Target,
    status: str | None,
    market_value_cents: int,
) -> None:
    plan, stop, decided = target
    threshold = plan.threshold
    if status != REPLACEABLE_ORDER_STATUS:
        shown = status or "unknown"
        reason = f"broker order status is {shown}, not {REPLACEABLE_ORDER_STATUS}"
        _record(sink, "StopReplaceSkipped", target, reason, order_status=shown)
        return
    # Never to or above the market: that is an exit, and exits are ADR-0017's and
    # the operator's capital decision, not a reconciliation routine's.
    if decided * threshold.quantity >= market_value_cents:
        price = _dollars(Decimal(market_value_cents) / threshold.quantity)
        reason = f"decided stop {_dollars(decided)} is at or above the price {price}"
        _record(sink, "StopReplaceRefused", target, reason, price=price)
        return
    key = free_broker_stop_order_key(graph, threshold.position_ref, threshold.ticker)
    try:
        fill = broker.replace_stop(stop.broker_order_id, decided, idempotency_key=key)
    except Exception as exc:
        _record(sink, "StopReplaceFailed", target, str(exc))
        return
    provenance = plan.provenance
    fill_node = write_stop_fill(
        graph, threshold, key, fill, decided, provenance=provenance
    )
    new = write_stop_order(
        graph, threshold, key, fill, decided, provenance=provenance, replaces=stop
    )
    graph.add_edge(fill_node, new, STOP_FILL_EDGE)
    link_positions(graph, threshold, new)
    mark_replaced(graph, stop, new)


def _record(
    sink: FaultSink, error_type: str, target: _Target, reason: str, **extra: str
) -> None:
    plan, stop, decided = target
    ticker = plan.threshold.ticker
    kept = _dollars(stop.stop_price_cents)
    sink.submit(
        AgentFault(
            source_agent="execution",
            source_module="agents.execution.broker_stop_realign",
            capability="replace_stop",
            severity="warning",
            error_type=error_type,
            message=f"stop for {ticker} not replaced: {reason}; {kept} stays live",
            context={
                "ticker": ticker,
                "position_ref": plan.threshold.position_ref,
                "broker_order_id": stop.broker_order_id,
                "stop_price_cents": stop.stop_price_cents,
                "decided_stop_cents": decided,
                "stop_pct": plan.threshold.stop_pct,
                "stop_pct_source": plan.stop_pct_source,
                "reason": reason,
                **extra,
            },
        )
    )


def _dollars(cents: int | Decimal) -> str:
    return str((Decimal(cents) / _CENTS).quantize(_DOLLARS))
