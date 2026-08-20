"""Stop threshold plans for fills awaiting monitor Position adoption.

Agent: execution
Role: derive protective-stop inputs from filled buy lineage without writing Position.
External I/O: injected GraphStore reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from agents.execution.broker_stop_thresholds import (
    BrokerStopThresholdPlan,
    StopPctSource,
)
from contracts.position_refs import position_ref_for_keys
from contracts.positions import PositionStopThreshold

if TYPE_CHECKING:
    from kernel import GraphStore, Node

_CENT_QUANT = Decimal("1")
_FILLED_STATUSES = frozenset({"filled"})


@dataclass(frozen=True)
class _PendingLot:
    position_key: str
    ticker: str
    quantity: int
    opened_price_cents: int
    stop_pct: float
    stop_pct_source: StopPctSource


def filled_entry_stop_thresholds(
    graph: GraphStore,
    *,
    broker_quantities: dict[str, int],
    blocked_tickers: frozenset[str],
    fallback_stop_pct: float,
) -> tuple[BrokerStopThresholdPlan, ...]:
    """Return stop plans for filled buys whose Position is not active yet."""
    by_ticker: dict[str, list[_PendingLot]] = {}
    for fill in graph.list_nodes("Fill"):
        lot = _pending_lot(graph, fill, fallback_stop_pct=fallback_stop_pct)
        if lot is None:
            continue
        if lot.ticker not in broker_quantities or lot.ticker in blocked_tickers:
            continue
        by_ticker.setdefault(lot.ticker, []).append(lot)
    plans: list[BrokerStopThresholdPlan] = []
    for ticker, lots in sorted(by_ticker.items()):
        sorted_lots = tuple(sorted(lots, key=lambda lot: lot.position_key))
        plan = _threshold_plan(ticker, sorted_lots)
        if plan is not None:
            plans.append(plan)
    return tuple(plans)


def _pending_lot(
    graph: GraphStore, fill: Node, *, fallback_stop_pct: float
) -> _PendingLot | None:
    if not _is_filled_buy(fill):
        return None
    ticker = str(fill.props.get("ticker", ""))
    source_run_id = _source_run_id(graph, fill)
    if not ticker or source_run_id is None:
        return None
    position_key = f"{source_run_id}:{ticker}"
    if graph.get_node("Position", position_key) is not None:
        return None
    try:
        quantity = _int_prop(fill, "quantity")
        opened_price_cents = _opened_price_cents(fill)
    except (TypeError, ValueError):
        return None
    if quantity <= 0:
        return None
    stop_pct, stop_pct_source = _stop_pct(
        _order_intent(graph, fill), fallback_stop_pct=fallback_stop_pct
    )
    return _PendingLot(
        position_key=position_key,
        ticker=ticker,
        quantity=quantity,
        opened_price_cents=opened_price_cents,
        stop_pct=stop_pct,
        stop_pct_source=stop_pct_source,
    )


def _threshold_plan(
    ticker: str, lots: tuple[_PendingLot, ...]
) -> BrokerStopThresholdPlan | None:
    stop_pcts = {lot.stop_pct for lot in lots}
    if len(stop_pcts) != 1:
        return None
    quantity = sum(lot.quantity for lot in lots)
    numerator = sum(lot.opened_price_cents * lot.quantity for lot in lots)
    opened = int(
        (Decimal(numerator) / Decimal(quantity)).quantize(
            _CENT_QUANT, rounding=ROUND_HALF_UP
        )
    )
    source: StopPctSource = (
        "fallback"
        if any(lot.stop_pct_source == "fallback" for lot in lots)
        else "position"
    )
    return BrokerStopThresholdPlan(
        threshold=PositionStopThreshold(
            ticker=ticker,
            quantity=quantity,
            position_ref=position_ref_for_keys(tuple(lot.position_key for lot in lots)),
            opened_price_cents=opened,
            stop_pct=next(iter(stop_pcts)),
        ),
        stop_pct_source=source,
    )


def _is_filled_buy(fill: Node) -> bool:
    status = fill.props.get("broker_status", fill.props.get("status"))
    return fill.props.get("side") == "buy" and status in _FILLED_STATUSES


def _source_run_id(graph: GraphStore, fill: Node) -> str | None:
    value = fill.props.get("source_run_id")
    if isinstance(value, str) and value:
        return value
    for order in graph.descendants(fill, max_depth=1, edge_types={"EXECUTES"}):
        for run in graph.descendants(order, max_depth=1, edge_types={"EMITTED_BY"}):
            return run.key
    return None


def _order_intent(graph: GraphStore, fill: Node) -> Node | None:
    orders = tuple(graph.descendants(fill, max_depth=1, edge_types={"EXECUTES"}))
    return orders[0] if orders else None


def _stop_pct(
    order: Node | None, *, fallback_stop_pct: float
) -> tuple[float, StopPctSource]:
    if order is None:
        return fallback_stop_pct, "fallback"
    value = order.props.get("stop_pct")
    if value is None:
        return fallback_stop_pct, "fallback"
    if isinstance(value, bool):
        return fallback_stop_pct, "fallback"
    return float(value), "position"


def _opened_price_cents(fill: Node) -> int:
    broker_price = fill.props.get("broker_price_cents")
    if broker_price is not None:
        return _int_value(broker_price)
    return _int_prop(fill, "price_cents")


def _int_prop(node: Node, name: str) -> int:
    return _int_value(node.props[name])


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        raise TypeError("bool is not an integer field")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise TypeError("expected integer-like graph property")
