"""Held-name barrier plans: the live stop and the declared target of each held name.

Agent: forecaster
Role: for each name the book holds (`contracts.positions.open_positions`, the book
      the analyst scored), read the stop the broker holds for it (the newest
      `BrokerStopOrder` execution placed under its position_ref, not cancelled or
      replaced) and the target its buy declared (an adopted holding's filled
      production buy, matched by the rule its stop is read by, DL-222/223; a
      PM-lineage Position's own `target_pct`), as the features of a held-name
      claim request (DL-310). Every held name gets a request; a stop or a target
      the graph does not give is left out of its features, so the claim's refusal
      names what was missing (FORE-FAIL-04).
External I/O: none (graph reads only: Position, BrokerStopOrder and, for an
      adopted holding, Fill each read once per pass).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from contracts.broker_stops import BROKER_STOP_ORDER_LABEL
from contracts.position_refs import position_ref_for_keys
from contracts.positions import POSITION_LABEL, is_active_position_node
from contracts.stop_width import ADOPTED_PROVENANCE, LineageFills, _equals_holding

if TYPE_CHECKING:
    from kernel import GraphStore, Node

#: The ForecastRequest subject of a held-name claim.
HELD_SUBJECT: Final = "position"
#: Append-only markers that end a stop placement's life (EXEC-OBS-03).
_ENDED = ("cancelled_at", "replaced_at")
_EXECUTES_EDGE = "EXECUTES"


def held_requests(graph: GraphStore) -> tuple[tuple[str, dict[str, float]], ...]:
    """``(ticker, features)`` for each held name, in ticker order.

    The features carry ``stop_price`` (the live stop, in dollars) and, when the
    buy's target is known, ``target_price`` and ``target_pct`` (its declared
    width): the claim measures both from its own last close.
    """
    by_ticker: dict[str, list[Node]] = {}
    for node in graph.list_nodes(POSITION_LABEL):
        if is_active_position_node(node):
            by_ticker.setdefault(str(node.props["ticker"]), []).append(node)
    if not by_ticker:
        return ()
    stops = _live_stops(graph)
    fills = LineageFills(graph)
    requests = []
    for ticker, nodes in sorted(by_ticker.items()):
        features: dict[str, float] = {}
        ref = position_ref_for_keys(tuple(node.key for node in nodes))
        if ref in stops:
            features["stop_price"] = stops[ref]
        target_pct = _declared_target_pct(graph, nodes, fills)
        if target_pct is not None:
            entry = int(nodes[0].props["opened_price_cents"]) / 100
            features["target_price"] = round(entry * (1 + target_pct), 4)
            features["target_pct"] = target_pct
        requests.append((ticker, features))
    return tuple(requests)


def _live_stops(graph: GraphStore) -> dict[str, float]:
    """position_ref -> the newest placement's stop price, if that one still lives."""
    newest: dict[str, Node] = {}
    for node in graph.list_nodes(BROKER_STOP_ORDER_LABEL):
        ref = str(node.props["position_ref"])
        if ref not in newest or str(node.props["placed_at"]) > str(
            newest[ref].props["placed_at"]
        ):
            newest[ref] = node
    return {
        ref: int(node.props["stop_price_cents"]) / 100
        for ref, node in newest.items()
        if not any(node.props.get(marker) for marker in _ENDED)
    }


def _declared_target_pct(
    graph: GraphStore, nodes: list[Node], fills: LineageFills
) -> float | None:
    """The target width the holding's buy declared, or None (one lot only)."""
    if len(nodes) != 1:
        return None
    position = nodes[0]
    if position.props.get("provenance") == ADOPTED_PROVENANCE:
        matches = sorted(
            (fill for fill in fills.nodes() if _equals_holding(fill, position)),
            key=lambda fill: (str(fill.props.get("submitted_at") or ""), fill.key),
        )
        if not matches:
            return None
        orders = graph.descendants(
            matches[-1], max_depth=1, edge_types={_EXECUTES_EDGE}
        )
        order = next(iter(orders), None)
        value = None if order is None else order.props.get("target_pct")
    else:
        value = position.props.get("target_pct")
    if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
        return None
    return float(value)
