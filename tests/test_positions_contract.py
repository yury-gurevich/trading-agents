"""Shared open-position contract tests.

Agent: contracts
Role: keep the cross-agent held-position read model consistent.
External I/O: none.
"""

from __future__ import annotations

from contracts.positions import active_position_nodes, open_position_tickers
from kernel import InMemoryGraphStore


def test_open_position_tickers_filters_closed_and_broker_inactive_nodes() -> None:
    graph = InMemoryGraphStore()
    active = _position(graph, "active:AAPL", "AAPL", 2)
    _position(graph, "closed:MSFT", "MSFT", 1, status="closed")
    _position(graph, "absent:IBM", "IBM", 1, broker_absent=True)
    _position(graph, "superseded:ORCL", "ORCL", 1, broker_superseded_by="new")
    closed_by_decision = _position(graph, "close:INTC", "INTC", 1)
    close = graph.merge_node("CloseDecision", "close:intc", {"decision": "close"})
    graph.add_edge(close, closed_by_decision, "CLOSES")

    assert active_position_nodes(graph) == (active,)
    assert open_position_tickers(graph) == ("AAPL",)


def _position(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    quantity: int,
    **props: object,
):
    return graph.merge_node(
        "Position",
        key,
        {"ticker": ticker, "quantity": quantity, **props},
    )
