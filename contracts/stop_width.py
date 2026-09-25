"""The one definition of a held position's decided stop width.

Agent: contracts
Role: resolve a Position's stop_pct from its PM lineage and name where it came from.
External I/O: injected GraphStore reads only.

The analyst's held-stop inputs, execution's stop placement and the monitor's
watchdog all call this, so they cannot disagree about a stop (DL-223). A
broker-adopted Position carries the monitor's fallback width, so its decided width
is read from the one filled production buy that equals it exactly (DL-222).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, NamedTuple

from contracts.broker_lifecycle import is_filled_buy_fill

if TYPE_CHECKING:
    from kernel import GraphStore, Node

StopWidthSource = Literal["lineage", "position", "fallback"]

ADOPTED_PROVENANCE = "reconciled-from-broker"
# Only a PM run's fills are production lineage; verification fills have no
# OrderIntent edge and must never be matched (S230 spec, traps).
PRODUCTION_RUN_PREFIX = "pm-run-"
_EXECUTES_EDGE = "EXECUTES"


class DecidedStop(NamedTuple):
    """A stop width and the source it was read from."""

    stop_pct: float
    source: StopWidthSource


def decided_stop_pct(
    graph: GraphStore, position: Node, *, fallback: float | None = None
) -> DecidedStop:
    """Return the stop width the PM decided for a held Position, and its source.

    An adopted Position reads `lineage` from the most recent filled production buy
    whose quantity and broker price equal it exactly; with no exact match it keeps
    the width it recorded at adoption and says `fallback`. Any other Position is
    its own `position` source. `fallback` applies only to a Position that records
    no width at all; without one, that Position raises ValueError.
    """
    recorded = _recorded_stop_pct(position)
    if position.props.get("provenance") == ADOPTED_PROVENANCE:
        decided = _lineage_stop_pct(graph, position)
        if decided is not None:
            return DecidedStop(decided, "lineage")
        return DecidedStop(_or_fallback(recorded, fallback), "fallback")
    if recorded is not None:
        return DecidedStop(recorded, "position")
    return DecidedStop(_or_fallback(None, fallback), "fallback")


def _recorded_stop_pct(position: Node) -> float | None:
    value = position.props.get("stop_pct")
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError("stop_pct")
    return float(value)


def _or_fallback(recorded: float | None, fallback: float | None) -> float:
    width = fallback if recorded is None else recorded
    if width is None:
        raise ValueError("position records no stop width and no fallback was given")
    return width


def _lineage_stop_pct(graph: GraphStore, position: Node) -> float | None:
    matches = sorted(
        (fill for fill in graph.list_nodes("Fill") if _equals_holding(fill, position)),
        key=lambda fill: (str(fill.props.get("submitted_at") or ""), fill.key),
    )
    if not matches:
        return None
    return _order_stop_pct(graph, matches[-1])


def _equals_holding(fill: Node, position: Node) -> bool:
    """Exact quantity AND exact broker price: never a guess across lots (DL-223)."""
    run_id = fill.props.get("source_run_id")
    quantity = _whole(fill.props.get("quantity"))
    price = _whole(fill.props.get("broker_price_cents"))
    return (
        quantity is not None
        and price is not None
        and fill.props.get("ticker") == position.props.get("ticker")
        and is_filled_buy_fill(fill)
        and isinstance(run_id, str)
        and run_id.startswith(PRODUCTION_RUN_PREFIX)
        and quantity == _whole(position.props.get("quantity"))
        and price == _whole(position.props.get("opened_price_cents"))
    )


def _order_stop_pct(graph: GraphStore, fill: Node) -> float | None:
    orders = graph.descendants(fill, max_depth=1, edge_types={_EXECUTES_EDGE})
    order = next(iter(orders), None)
    value = None if order is None else order.props.get("stop_pct")
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def _whole(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value
