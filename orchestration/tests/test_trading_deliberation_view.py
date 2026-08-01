"""Deliberation observatory view tests.

Agent: orchestration
Role: prove the deliberation stage renderer handles optional narrative output.
External I/O: none.
"""

from __future__ import annotations

from kernel import InMemoryGraphStore
from orchestration.packs.trading_deliberation_view import deliberation


def test_deliberation_view_handles_missing_narrative() -> None:
    graph = InMemoryGraphStore()
    node = graph.merge_node(
        "DeliberationRun",
        "run",
        {"verdicts": {}, "vetoed_tickers": (), "debates": {}},
    )

    view = deliberation(graph, node)

    assert view.outputs == ("reviewed=0  vetoed=0",)
