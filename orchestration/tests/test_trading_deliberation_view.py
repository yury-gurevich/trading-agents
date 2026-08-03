"""Deliberation observatory view tests.

Agent: orchestration
Role: prove the deliberation stage renderer handles optional narrative output.
External I/O: none.
"""

from __future__ import annotations

from kernel import InMemoryGraphStore
from orchestration.observatory import breaches
from orchestration.packs.trading_deliberation_view import deliberation


def test_deliberation_view_handles_missing_narrative() -> None:
    graph = InMemoryGraphStore()
    node = graph.merge_node(
        "DeliberationRun",
        "run",
        {
            "verdicts": {},
            "vetoed_tickers": (),
            "debates": {},
            "real_debate_count": 0,
            "failed_open_count": 0,
            "failed_open_tickers": (),
        },
    )

    view = deliberation(graph, node)

    assert view.outputs == (
        "reviewed=0  vetoed=0",
        "real_debates=0  failed_open=0",
    )
    assert breaches(view) == ()


def test_old_empty_transcript_shape_fails_deliberation_checks() -> None:
    """D4 DL-70: the old fail-open artifact shape cannot satisfy the gate."""
    graph = InMemoryGraphStore()
    node = graph.merge_node(
        "DeliberationRun",
        "run",
        {
            "verdicts": {"AAPL": "uphold"},
            "vetoed_tickers": (),
            "debates": {"AAPL": {"verdict": "uphold", "turns": []}},
            "transcript": (),
        },
    )

    found = breaches(deliberation(graph, node))

    assert {breach.key for breach in found} == {
        "debate_coverage",
        "failed_open_count",
    }
