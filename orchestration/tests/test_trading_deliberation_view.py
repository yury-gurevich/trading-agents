"""Deliberation observatory view tests.

Agent: orchestration
Role: prove the deliberation stage renderer handles optional narrative output.
External I/O: none.
"""

from __future__ import annotations

from kernel import InMemoryGraphStore
from orchestration.observatory import breaches
from orchestration.packs.trading_deliberation_view import deliberation


def _link_execution(graph: InMemoryGraphStore, node_key: str) -> None:
    pm_run = graph.merge_node("PMRun", f"pm-{node_key}", {})
    delib = graph.get_node("DeliberationRun", node_key)
    assert delib is not None
    execution = graph.merge_node(
        "ExecutionRun",
        f"exec-{node_key}",
        {"deliberation_posture": "binding", "deliberation_status": "applied"},
    )
    graph.add_edge(pm_run, delib, "DELIBERATED_BY")
    graph.add_edge(pm_run, execution, "EXECUTED_BY")


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
    _link_execution(graph, "run")

    view = deliberation(graph, node)

    assert view.outputs == (
        "reviewed=0  vetoed=0",
        "real_debates=0  failed_open=0  orphaned_replies=n/a",
        "posture=binding  status=applied",
    )
    assert breaches(view) == ()


def test_deliberation_view_renders_orphaned_reply_count() -> None:
    """DLIB-OBS-04: late peer-reply evidence is visible when recorded."""
    graph = InMemoryGraphStore()
    node = graph.merge_node(
        "DeliberationRun",
        "run",
        {
            "verdicts": {"AAPL": "uphold"},
            "vetoed_tickers": (),
            "debates": {"AAPL": {"verdict": "uphold", "turns": []}},
            "real_debate_count": 1,
            "failed_open_count": 0,
            "orphaned_reply_count": 2,
            "failed_open_tickers": (),
        },
    )
    _link_execution(graph, "run")

    view = deliberation(graph, node)

    assert view.observed["orphaned_reply_count"] == 2
    assert any("orphaned_replies=2" in output for output in view.outputs)


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
    _link_execution(graph, "run")

    found = breaches(deliberation(graph, node))

    assert {breach.key for breach in found} == {
        "debate_coverage",
        "failed_open_count",
    }
