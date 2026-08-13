"""GraphStore partial-fill completion merge tests.

Agent: kernel
Role: prove the graph merge exception is limited to one broker completion.
External I/O: none.
"""

from __future__ import annotations

import pytest
from tests.graph_postgres_fakes import store as fake_postgres_store

from kernel import InMemoryGraphStore


def test_in_memory_allows_only_partial_fill_completion_props() -> None:
    graph = InMemoryGraphStore()

    _partial(graph)
    completed = graph.merge_node("Fill", "fill", _completed())

    assert completed.props["broker_status"] == "filled"
    assert completed.props["broker_price_cents"] == 10200
    assert completed.props["broker_status_refreshed_at"] == "new"
    assert completed.props["realized_pnl_cents"] == 2000
    with pytest.raises(ValueError, match="cannot be overwritten"):
        graph.merge_node("Fill", "fill", {"broker_status": "partial"})


def test_postgres_allows_only_partial_fill_completion_props(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph, _connection = fake_postgres_store(monkeypatch)

    _partial(graph)
    completed = graph.merge_node("Fill", "fill", _completed())

    assert completed.props["broker_status"] == "filled"
    with pytest.raises(ValueError, match="cannot be overwritten"):
        graph.merge_node("Fill", "fill", {"broker_price_cents": 10135})


def _partial(graph: InMemoryGraphStore) -> None:
    graph.merge_node(
        "Fill",
        "fill",
        {
            "broker_status": "partial",
            "broker_price_cents": 10135,
            "broker_status_refreshed_at": "old",
            "realized_pnl_cents": 1350,
        },
    )


def _completed() -> dict[str, object]:
    return {
        "broker_status": "filled",
        "broker_price_cents": 10200,
        "broker_status_refreshed_at": "new",
        "realized_pnl_cents": 2000,
    }
