"""MarketData lookup helpers for Portfolio Manager graph-backed context.

Agent: portfolio_manager
Role: read the full provider MarketData payload for the recommendation run.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.provider import MARKET_DATA_LABEL, MarketData

if TYPE_CHECKING:
    from kernel import GraphStore


def market_data_for_run(graph: GraphStore, run_id: str) -> MarketData | None:
    """Return the MarketData node keyed by *run_id*, or None when absent."""
    node = graph.get_node(MARKET_DATA_LABEL, f"market-data:{run_id}")
    if node is None:
        return None
    return MarketData.model_validate(node.props["snapshot"])
