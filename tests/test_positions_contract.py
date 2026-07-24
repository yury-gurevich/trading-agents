"""Shared open-position contract tests.

Agent: contracts
Role: keep the cross-agent held-position read model consistent.
External I/O: none.
"""

from __future__ import annotations

from contracts.positions import (
    active_position_nodes,
    open_positions,
    position_basis_for_ref,
)
from kernel import InMemoryGraphStore


def test_open_position_tickers_filter_only_broker_inactive_nodes() -> None:
    """ADR-0015 s1: close decisions are intent; broker evidence closes them."""
    graph = InMemoryGraphStore()
    active = _position(graph, "active:AAPL", "AAPL", 2)
    _position(graph, "closed:MSFT", "MSFT", 1, status="closed")
    _position(graph, "absent:IBM", "IBM", 1, broker_absent=True)
    _position(graph, "superseded:ORCL", "ORCL", 1, broker_superseded_by="new")
    closed_by_decision = _position(graph, "close:INTC", "INTC", 1)
    close = graph.merge_node("CloseDecision", "close:intc", {"decision": "close"})
    graph.add_edge(close, closed_by_decision, "CLOSES")

    assert active_position_nodes(graph) == (active, closed_by_decision)
    positions = open_positions(graph)
    assert [(position.ticker, position.quantity) for position in positions] == [
        ("AAPL", 2),
        ("INTC", 1),
    ]
    assert all(position.position_ref for position in positions)


def test_open_positions_ref_is_stable_for_same_nodes_and_changes_with_nodes() -> None:
    """ADR-0015 section 1: lineage decisions do not alter openness; broker nodes do."""
    graph = InMemoryGraphStore()
    _position(graph, "b:AAPL", "AAPL", 2)
    first = _position(graph, "a:AAPL", "AAPL", 3)

    unchanged = open_positions(graph)[0].position_ref
    graph.add_edge(
        graph.merge_node("CloseDecision", "close:a", {"decision": "close"}),
        first,
        "CLOSES",
    )
    assert open_positions(graph)[0].position_ref == unchanged
    _position(graph, "c:AAPL", "AAPL", 3)

    assert open_positions(graph)[0].position_ref != unchanged


def test_position_basis_resolves_contributing_lots_by_ref() -> None:
    graph = InMemoryGraphStore()
    _position(graph, "msft", "MSFT", 1, opened_price_cents=9900)
    _position(graph, "b:AAPL", "AAPL", 2, opened_price_cents=10100)
    _position(graph, "a:AAPL", "AAPL", 3, opened_price_cents=10000)
    ref = next(p.position_ref for p in open_positions(graph) if p.ticker == "AAPL")

    basis = position_basis_for_ref(graph, position_ref=ref, ticker="AAPL")

    assert basis is not None
    assert basis.quantity == 5
    lots = [(lot.node_key, lot.quantity, lot.opened_price_cents) for lot in basis.lots]
    assert lots == [
        ("a:AAPL", 3, 10000),
        ("b:AAPL", 2, 10100),
    ]


def test_position_basis_returns_none_when_ref_or_open_price_is_unknown() -> None:
    graph = InMemoryGraphStore()
    _position(graph, "a:AAPL", "AAPL", 3)
    ref = open_positions(graph)[0].position_ref

    assert position_basis_for_ref(graph, position_ref="unknown", ticker="AAPL") is None
    assert position_basis_for_ref(graph, position_ref=ref, ticker="MSFT") is None
    assert position_basis_for_ref(graph, position_ref=ref, ticker="AAPL") is None


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
