"""Position lifecycle read model.

Agent: surfaces
Role: project entry-to-exit position lineage for operator surfaces.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from surfaces.queries._graph import nodes_by_label

if TYPE_CHECKING:
    from kernel import GraphStore, Node


@dataclass(frozen=True)
class PositionLifecycle:
    """Full available lifecycle details for one Position node."""

    position_id: str
    ticker: str
    quantity: int
    opened_price_cents: int
    status: str
    close_trigger: str | None
    run_id: str | None
    recommendation_confidence: float | None
    narrative_text: str | None


def position_lifecycle(graph: GraphStore, position_id: str) -> PositionLifecycle | None:
    """Traverse the full entry-to-exit chain for one position."""
    position = graph.get_node("Position", position_id)
    if position is None:
        return None
    fill = _linked(graph, position, "OPENS", "Fill", upstream=True)
    order = _linked(graph, fill, "EXECUTES", "OrderIntent")
    pm_run = _linked(graph, order, "EMITTED_BY", "PMRun")
    recommendation = _linked(graph, order, "APPROVES", "Recommendation")
    close = _linked(graph, position, "CLOSES", "CloseDecision", upstream=True)
    narrative = _linked(graph, position, "NARRATES", "TradeNarrative", upstream=True)
    return PositionLifecycle(
        position_id=position.key,
        ticker=str(position.props.get("ticker", "")),
        quantity=int(position.props.get("quantity", 0)),
        opened_price_cents=int(position.props.get("opened_price_cents", 0)),
        status=str(position.props.get("status", "open")) if close is None else "closed",
        close_trigger=_text(close, "trigger"),
        run_id=_run_id(position, pm_run),
        recommendation_confidence=_confidence(recommendation),
        narrative_text=_text(narrative, "summary"),
    )


def all_position_lifecycles(graph: GraphStore) -> tuple[PositionLifecycle, ...]:
    """Return lifecycle details for all Position nodes in the graph."""
    lifecycles: list[PositionLifecycle] = []
    for position in nodes_by_label(graph, "Position"):
        lifecycle = position_lifecycle(graph, position.key)
        if lifecycle is not None:
            lifecycles.append(lifecycle)
    return tuple(lifecycles)


def _linked(
    graph: GraphStore,
    node: Node | None,
    edge_type: str,
    label: str,
    *,
    upstream: bool = False,
) -> Node | None:
    if node is None:
        return None
    walk = graph.ancestors if upstream else graph.descendants
    for found in walk(node, max_depth=1, edge_types={edge_type}):
        if found.label == label:
            return found
    return None


def _run_id(position: Node, pm_run: Node | None) -> str | None:
    raw = pm_run.key if pm_run is not None else position.props.get("run_id")
    return None if raw is None else str(raw)


def _confidence(recommendation: Node | None) -> float | None:
    raw = None if recommendation is None else recommendation.props.get("confidence")
    return None if raw is None else float(raw)


def _text(node: Node | None, prop: str) -> str | None:
    raw = None if node is None else node.props.get(prop)
    return None if raw is None else str(raw)
