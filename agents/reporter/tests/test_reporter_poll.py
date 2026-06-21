"""Reporter graph-poll find_pending + report_monitor_node tests.

Agent: reporter
Role: verify the reporter finds unreported MonitorRun nodes and builds their run
      snapshot from the graph, linking a processed edge so each is reported once.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.reporter.poll import find_pending, report_monitor_node
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from kernel import GraphStore, Node

_PM_RUN = "pm-run-1"


def _seed_monitor_run(graph: GraphStore, *, with_pm_run: bool = True) -> Node:
    if with_pm_run:
        graph.merge_node("PMRun", _PM_RUN, {"approved_count": 0})
    return graph.merge_node("MonitorRun", "monitor-1", {"source_run_id": _PM_RUN})


def test_find_pending_returns_unreported_monitor_run() -> None:
    graph = InMemoryGraphStore()
    _seed_monitor_run(graph)
    assert len(find_pending(graph)) == 1


def test_find_pending_empty_when_no_monitor_run() -> None:
    assert find_pending(InMemoryGraphStore()) == []


def test_report_monitor_node_writes_snapshot_and_links() -> None:
    graph = InMemoryGraphStore()
    node = _seed_monitor_run(graph)
    report_monitor_node(node, graph=graph)
    assert graph.get_node("Snapshot", f"snapshot:{_PM_RUN}") is not None
    assert find_pending(graph) == []


def test_report_monitor_node_handles_missing_pm_run() -> None:
    graph = InMemoryGraphStore()
    node = _seed_monitor_run(graph, with_pm_run=False)
    report_monitor_node(node, graph=graph)
    # build_snapshot writes a degraded Snapshot even with no PMRun, so the run is
    # still marked reported and not re-polled.
    assert graph.get_node("Snapshot", f"snapshot:{_PM_RUN}") is not None
    assert find_pending(graph) == []
