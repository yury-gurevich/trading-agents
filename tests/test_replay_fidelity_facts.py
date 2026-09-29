"""The exported book is a whole, read-only GraphStore for the fleet's own readers.

Agent: tooling
Role: prove the S237 view keeps the port's shape, serves its facts, and refuses the
      writes and walks an export cannot answer.
External I/O: none.
"""

from __future__ import annotations

import inspect

import pytest
from scripts.replay_fidelity_facts import ExportedFacts

from kernel.graph import GraphStore, Node

HELD = Node("Position", "pos-aapl", {"ticker": "AAPL"})
BOOK = Node("BrokerPositionSnapshot", "snap-1", {"equity_cents": 1})
VIEW = ExportedFacts((HELD, BOOK))


def _port_methods() -> tuple[str, ...]:
    return tuple(
        name
        for name, member in vars(GraphStore).items()
        if inspect.isfunction(member) and not name.startswith("_")
    )


def test_the_view_has_every_graph_store_method_with_the_ports_signature() -> None:
    """The cast is gone, so nothing but this test holds the view to the port."""
    methods = _port_methods()
    assert set(methods) == {
        "merge_node",
        "add_edge",
        "get_node",
        "list_nodes",
        "keys_without_edge",
        "ancestors",
        "descendants",
    }
    for name in methods:
        port = inspect.signature(getattr(GraphStore, name))
        view = inspect.signature(getattr(ExportedFacts, name))
        assert view == port, name


def test_the_view_serves_the_exported_facts_by_label_and_key() -> None:
    assert VIEW.list_nodes("Position") == (HELD,)
    assert VIEW.list_nodes("Fill") == ()
    assert VIEW.get_node("BrokerPositionSnapshot", "snap-1") == BOOK
    assert VIEW.get_node("Position", "pos-msft") is None
    assert VIEW.get_node("Fill", "pos-aapl") is None


def test_the_view_refuses_writes() -> None:
    with pytest.raises(PermissionError, match=r"merge_node\(Position, pos-x\)"):
        VIEW.merge_node("Position", "pos-x", {})
    with pytest.raises(PermissionError, match="add_edge"):
        VIEW.add_edge(BOOK, HELD, "HOLDS")


def test_the_view_refuses_walks_it_cannot_answer() -> None:
    """No edges were exported: an empty walk would read as a fact, so it is refused."""
    with pytest.raises(PermissionError, match="ancestors"):
        VIEW.ancestors(HELD, max_depth=1)
    with pytest.raises(PermissionError, match="descendants"):
        VIEW.descendants(HELD, max_depth=1)
    with pytest.raises(PermissionError, match=r"keys_without_edge\(Position, OPENS in"):
        VIEW.keys_without_edge("Position", "OPENS", downstream=False)
