"""The snapshot's readers over S253's book metrics.

Agent: orchestration
Role: prove the trace and the observatory print the new counts and tolerate absence.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.reporter.result import build_snapshot
from agents.reporter.tests.book_fixtures import (
    REPORTED_RUN,
    SETTINGS,
    pm_run,
    seed_sched_2026_10_01,
)
from kernel import InMemoryGraphStore, Node
from orchestration import batch_trace
from orchestration.packs.trading_observatory_views import reporter

if TYPE_CHECKING:
    import pytest


def test_the_trace_and_the_observatory_read_the_new_snapshot(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """RPT-OUT-02: both readers print the window's counts and the outcomes."""
    graph = InMemoryGraphStore()
    seed_sched_2026_10_01(graph)
    build_snapshot(graph, REPORTED_RUN, settings=SETTINGS)
    snapshot = _snapshot_node(graph, REPORTED_RUN)

    _trace(monkeypatch, graph, snapshot)
    out = capsys.readouterr().out
    view = reporter(graph, snapshot)

    assert "open=1.0  closed=3.0  profit_factor=0.00  expectancy_cents=-3632" in out
    assert "1 positions opened; 3 closed;" in out
    assert view.outputs[0] == "open=1.0  closed=3.0"


def test_the_readers_do_not_raise_on_absent_counts(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """RPT-NEV-03: a run with no `created_at` has no counts; neither reader raises."""
    graph = InMemoryGraphStore()
    pm_run(graph, "undated", None)
    build_snapshot(graph, "undated", settings=SETTINGS)
    snapshot = _snapshot_node(graph, "undated")

    _trace(monkeypatch, graph, snapshot)
    out = capsys.readouterr().out
    view = reporter(graph, snapshot)

    assert "open=?  closed=?  profit_factor=unavailable" in out
    assert view.outputs[0] == "open=None  closed=None"


def _snapshot_node(graph: InMemoryGraphStore, run_id: str) -> Node:
    node = graph.get_node("Snapshot", f"snapshot:{run_id}")
    assert node is not None
    return node


def _trace(
    monkeypatch: pytest.MonkeyPatch, graph: InMemoryGraphStore, snapshot: Node
) -> None:
    request = graph.merge_node("RunRequest", "run-request:readers", {})
    chain = {"RunRequest": request, "Snapshot": snapshot}
    monkeypatch.setattr(batch_trace, "walk_chain", lambda *_args: chain)
    batch_trace.print_trace(graph, "readers")
