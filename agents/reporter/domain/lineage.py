"""Reporter graph traversal helpers.

Agent: reporter
Role: collect read-only provenance legs used by metrics and narratives.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from kernel import GraphStore, Node

EMITTED_BY = "EMITTED_BY"
EXECUTES = "EXECUTES"
OPENS = "OPENS"
APPROVES = "APPROVES"
DERIVED_FROM = "DERIVED_FROM"
SURVIVED = "SURVIVED"
CLOSES = "CLOSES"
REJECTED_IN = "REJECTED_IN"


@dataclass(frozen=True)
class RunLineage:
    """The reporter's run-level view over upstream provenance."""

    orders: tuple[Node, ...]
    fills: tuple[Node, ...]
    positions: tuple[Node, ...]
    recommendations: tuple[Node, ...]
    rejections: tuple[Node, ...]
    close_decisions: tuple[Node, ...]
    scan_runs: tuple[Node, ...]
    market_snapshots: tuple[Node, ...]


@dataclass(frozen=True)
class TradeLineage:
    """The reporter's one-position graph path."""

    position: Node
    fill: Node | None
    order_intent: Node | None
    recommendation: Node | None
    candidate: Node | None
    scan_run: Node | None
    close_decision: Node | None


def collect_run_lineage(graph: GraphStore, pm_run: Node) -> RunLineage:
    """Collect all graph nodes needed for a run snapshot."""
    orders = _unique(graph.ancestors(pm_run, max_depth=1, edge_types={EMITTED_BY}))
    fills = _unique(
        fill
        for order in orders
        for fill in graph.ancestors(order, max_depth=1, edge_types={EXECUTES})
    )
    positions = _unique(
        position
        for fill in fills
        for position in graph.descendants(fill, max_depth=1, edge_types={OPENS})
    )
    recommendations = _unique(
        rec
        for order in orders
        for rec in graph.descendants(order, max_depth=1, edge_types={APPROVES})
    )
    close_decisions = _unique(
        close
        for position in positions
        for close in graph.ancestors(position, max_depth=1, edge_types={CLOSES})
    )
    scan_runs, market_snapshots = _market_lineage(graph, recommendations)
    return RunLineage(
        orders=orders,
        fills=fills,
        positions=positions,
        recommendations=recommendations,
        rejections=_unique(
            graph.ancestors(pm_run, max_depth=1, edge_types={REJECTED_IN})
        ),
        close_decisions=close_decisions,
        scan_runs=scan_runs,
        market_snapshots=market_snapshots,
    )


def collect_trade_lineage(graph: GraphStore, position: Node) -> TradeLineage:
    """Collect the graph path for one position narrative."""
    fill = _first(graph.ancestors(position, max_depth=1, edge_types={OPENS}))
    order = (
        None
        if fill is None
        else _first(graph.descendants(fill, max_depth=1, edge_types={EXECUTES}))
    )
    recommendation = (
        None
        if order is None
        else _first(graph.descendants(order, max_depth=1, edge_types={APPROVES}))
    )
    candidate = (
        None
        if recommendation is None
        else _first(
            graph.descendants(recommendation, max_depth=1, edge_types={DERIVED_FROM})
        )
    )
    scan_run = (
        None
        if candidate is None
        else _first(graph.descendants(candidate, max_depth=1, edge_types={SURVIVED}))
    )
    return TradeLineage(
        position=position,
        fill=fill,
        order_intent=order,
        recommendation=recommendation,
        candidate=candidate,
        scan_run=scan_run,
        close_decision=_first(
            graph.ancestors(position, max_depth=1, edge_types={CLOSES})
        ),
    )


def run_id(position: Node) -> str:
    """Return a position's PM run id, falling back to the key prefix."""
    return str(position.props.get("run_id", run_id_from_position_id(position.key)))


def run_id_from_position_id(position_id: str) -> str:
    """Return the PM run id prefix from a Position key."""
    return position_id.split(":", 1)[0]


def _market_lineage(
    graph: GraphStore, recommendations: tuple[Node, ...]
) -> tuple[tuple[Node, ...], tuple[Node, ...]]:
    scan_runs: list[Node] = []
    snapshots: list[Node] = []
    for recommendation in recommendations:
        candidate = _first(
            graph.descendants(recommendation, max_depth=1, edge_types={DERIVED_FROM})
        )
        if candidate is None:
            continue
        scan_run = _first(
            graph.descendants(candidate, max_depth=1, edge_types={SURVIVED})
        )
        if scan_run is None:
            continue
        scan_runs.append(scan_run)
        snapshots.extend(
            graph.descendants(scan_run, max_depth=1, edge_types={DERIVED_FROM})
        )
    return _unique(scan_runs), _unique(snapshots)


def _unique(nodes: Iterable[Node]) -> tuple[Node, ...]:
    out: dict[tuple[str, str], Node] = {}
    for node in nodes:
        out[(node.label, node.key)] = node
    return tuple(out.values())


def _first(nodes: Iterable[Node]) -> Node | None:
    return next(iter(nodes), None)
