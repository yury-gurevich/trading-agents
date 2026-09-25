"""Execution-owned broker-stop threshold planning.

Agent: execution
Role: derive stop placement inputs for active positions, with explicit fallback use.
External I/O: injected GraphStore reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from agents.execution.broker_stop_types import (
    BrokerStopThresholdError,
    BrokerStopThresholdPlan,
    BrokerStopThresholdPlans,
)
from contracts.positions import (
    PositionStopThreshold,
    active_position_nodes,
    open_positions,
)
from contracts.stop_width import decided_stop_pct

if TYPE_CHECKING:
    from agents.execution.broker_stop_types import StopPctSource
    from contracts.common import Ticker
    from kernel import GraphStore, Node

_CENT_QUANT = Decimal("1")
# A multi-lot plan reports its weakest source: any fallback lot makes it fallback.
_SOURCE_PRECEDENCE: tuple[StopPctSource, ...] = ("fallback", "lineage", "position")


@dataclass(frozen=True)
class _Lot:
    quantity: int
    opened_price_cents: int
    stop_pct: float
    stop_pct_source: StopPctSource


def broker_stop_thresholds(
    graph: GraphStore, *, fallback_stop_pct: float
) -> BrokerStopThresholdPlans:
    """Return per-ticker stop thresholds, falling back when stop_pct is absent."""
    positions_by_ticker = _active_nodes_by_ticker(graph)
    refs_by_ticker = {
        position.ticker: position.position_ref for position in open_positions(graph)
    }
    plans: list[BrokerStopThresholdPlan] = []
    errors: list[BrokerStopThresholdError] = []
    for ticker, nodes in sorted(positions_by_ticker.items()):
        try:
            plans.append(
                _threshold_plan_or_raise(
                    graph,
                    ticker,
                    tuple(sorted(nodes, key=lambda node: node.key)),
                    refs_by_ticker[ticker],
                    fallback_stop_pct=fallback_stop_pct,
                )
            )
        except ValueError as exc:
            errors.append(BrokerStopThresholdError(ticker=ticker, reason=str(exc)))
    return BrokerStopThresholdPlans(plans=tuple(plans), errors=tuple(errors))


def _active_nodes_by_ticker(graph: GraphStore) -> dict[Ticker, list[Node]]:
    nodes_by_ticker: dict[Ticker, list[Node]] = {}
    for node in active_position_nodes(graph):
        ticker = str(node.props.get("ticker", ""))
        if ticker:
            nodes_by_ticker.setdefault(ticker, []).append(node)
    return nodes_by_ticker


def _threshold_plan_or_raise(
    graph: GraphStore,
    ticker: Ticker,
    nodes: tuple[Node, ...],
    position_ref: str,
    *,
    fallback_stop_pct: float,
) -> BrokerStopThresholdPlan:
    lots = tuple(_lot(graph, ticker, node, fallback_stop_pct) for node in nodes)
    stop_pcts = {lot.stop_pct for lot in lots}
    if len(stop_pcts) != 1:
        raise ValueError(f"active lots for {ticker} carry different stop_pct values")
    quantity = sum(lot.quantity for lot in lots)
    if quantity <= 0:
        raise ValueError(f"active lots for {ticker} carry non-positive quantity")
    numerator = sum(lot.opened_price_cents * lot.quantity for lot in lots)
    opened = int(
        (Decimal(numerator) / Decimal(quantity)).quantize(
            _CENT_QUANT, rounding=ROUND_HALF_UP
        )
    )
    sources = {lot.stop_pct_source for lot in lots}
    source = next(name for name in _SOURCE_PRECEDENCE if name in sources)
    return BrokerStopThresholdPlan(
        threshold=PositionStopThreshold(
            ticker=ticker,
            quantity=quantity,
            position_ref=position_ref,
            opened_price_cents=opened,
            stop_pct=next(iter(stop_pcts)),
        ),
        stop_pct_source=source,
        derived_from="active_position",
    )


def _lot(
    graph: GraphStore, ticker: Ticker, node: Node, fallback_stop_pct: float
) -> _Lot:
    try:
        quantity = _int_prop(node, "quantity")
        opened = _int_prop(node, "opened_price_cents")
        stop_pct, source = decided_stop_pct(graph, node, fallback=fallback_stop_pct)
    except (TypeError, ValueError) as exc:
        message = f"active lot for {ticker} lacks stop threshold inputs"
        raise ValueError(message) from exc
    return _Lot(
        quantity=quantity,
        opened_price_cents=opened,
        stop_pct=stop_pct,
        stop_pct_source=source,
    )


def _int_prop(node: Node, name: str) -> int:
    value = node.props[name]
    if isinstance(value, bool):
        raise TypeError(name)
    return int(value)
