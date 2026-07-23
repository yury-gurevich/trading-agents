"""Graph-derived PortfolioState for PM risk gates.

Agent: portfolio_manager
Role: rebuild held-position awareness from open Position nodes before sizing.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.portfolio_manager.portfolio import PortfolioState
from contracts.common import Money
from contracts.positions import open_positions

if TYPE_CHECKING:
    from decimal import Decimal

    from kernel import GraphStore


def portfolio_from_graph(graph: GraphStore, starting_cash: Decimal) -> PortfolioState:
    """Build PM's starting portfolio from active graph Position nodes."""
    holdings = open_positions(graph)
    positions = {position.ticker: position.quantity for position in holdings}
    position_refs = {position.ticker: position.position_ref for position in holdings}
    return PortfolioState(
        cash=Money(amount=starting_cash),
        positions=positions,
        position_refs=position_refs,
    )
