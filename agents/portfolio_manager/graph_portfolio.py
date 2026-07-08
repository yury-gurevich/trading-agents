"""Graph-derived PortfolioState for PM risk gates.

Agent: portfolio_manager
Role: rebuild held-position awareness from open Position nodes before sizing.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.portfolio_manager.portfolio import PortfolioState
from contracts.common import Money

if TYPE_CHECKING:
    from decimal import Decimal

    from kernel import GraphStore, Node


def portfolio_from_graph(graph: GraphStore, starting_cash: Decimal) -> PortfolioState:
    """Build PM's starting portfolio from active graph Position nodes."""
    positions: dict[str, int] = {}
    for node in graph.list_nodes("Position"):
        if not _is_active_position(graph, node):
            continue
        ticker = str(node.props["ticker"])
        positions[ticker] = positions.get(ticker, 0) + int(node.props["quantity"])
    return PortfolioState(cash=Money(amount=starting_cash), positions=positions)


def _is_active_position(graph: GraphStore, node: Node) -> bool:
    if node.props.get("status", "open") != "open":
        return False
    if node.props.get("broker_absent") or node.props.get("broker_superseded_by"):
        return False
    closes = graph.ancestors(node, max_depth=1, edge_types={"CLOSES"})
    return not any(close.props.get("decision") == "close" for close in closes)
