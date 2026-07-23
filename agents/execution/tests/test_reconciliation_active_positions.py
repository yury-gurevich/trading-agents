"""Execution reconciliation active-position boundary tests.

Agent: execution
Role: prove inactive graph positions do not create broker divergences.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.broker import BrokerPosition
from agents.execution.reconciliation_store import position_divergences
from kernel import InMemoryGraphStore, Node


def test_position_divergences_treats_close_decision_as_active_lineage() -> None:
    """ADR-0015 s1: close intent stays active while the broker still holds it."""
    graph = InMemoryGraphStore()
    _position(graph, "active:AAPL", "AAPL", 1)
    _position(graph, "closed:MSFT", "MSFT", 1, status="closed")
    _position(graph, "absent:IBM", "IBM", 1, broker_absent=True)
    _position(graph, "superseded:ORCL", "ORCL", 1, broker_superseded_by="new")
    closed_by_decision = _position(graph, "close-edge:INTC", "INTC", 1)
    close = graph.merge_node("CloseDecision", "close:INTC", {"decision": "close"})
    graph.add_edge(close, closed_by_decision, "CLOSES")

    assert (
        position_divergences(
            graph,
            (
                BrokerPosition("AAPL", 1, 10000, 10000),
                BrokerPosition("INTC", 1, 10000, 10000),
            ),
        )
        == ()
    )


def _position(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    quantity: int,
    **extra: object,
) -> Node:
    props = {
        "ticker": ticker,
        "quantity": quantity,
        "opened_price_cents": 10000,
        "status": "open",
        **extra,
    }
    return graph.merge_node("Position", key, props)
