"""Monitor position-sync work-item branch tests.

Agent: monitor
Role: prove mixed sync/evaluate dispatch and orphan snapshot behavior.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import agents.monitor.poll as poll
from agents.monitor.poll import MonitorWorkItem, find_pending_work, process_work_item
from agents.monitor.reconcile import reconcile_positions_from_snapshot
from agents.monitor.settings import MonitorSettings
from agents.monitor.tests.position_sync_helpers import snapshot
from contracts.position_sync import SNAPSHOT_LABEL, SNAPSHOT_SYNC_EDGE
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    import pytest


def test_work_items_prioritize_sync_before_tail_evaluation() -> None:
    """MON-TRG-04 / MON-STA-02: sync work is before tail monitor work."""
    graph = InMemoryGraphStore()
    sync = snapshot(graph, "mixed", holdings=())
    tail = graph.merge_node("ExecutionRun", "execution-run:mixed", {})

    work = find_pending_work(graph)

    assert [(item.kind, item.node) for item in work] == [
        ("position_sync", sync),
        ("evaluate", tail),
    ]


def test_process_work_item_dispatches_both_kinds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MON-TRG-04 / MON-STA-02: planted work items hit both dispatch arms."""
    graph = InMemoryGraphStore()
    sync = snapshot(graph, "dispatch", holdings=())
    tail = graph.merge_node("ExecutionRun", "execution-run:dispatch", {})
    seen: dict[str, object] = {}

    def fake_monitor(node: object, **kwargs: object) -> None:
        seen["tail_node"] = node
        seen["tail_graph"] = kwargs["graph"]

    monkeypatch.setattr(poll, "monitor_pm_node", fake_monitor)

    process_work_item(MonitorWorkItem("position_sync", sync), graph=graph)
    process_work_item(MonitorWorkItem("evaluate", tail), graph=graph)

    assert graph.descendants(sync, max_depth=1, edge_types={SNAPSHOT_SYNC_EDGE})
    assert seen == {"tail_node": tail, "tail_graph": graph}


def test_orphan_snapshot_sync_marker_has_no_run_request_edge() -> None:
    """MON-STA-02: planted orphan snapshot is marked without fake RunRequest."""
    graph = InMemoryGraphStore()
    sync = graph.merge_node(
        SNAPSHOT_LABEL,
        "snapshot:orphan",
        {"run_id": "orphan", "status": "stale", "holdings": ()},
    )

    process_work_item(MonitorWorkItem("position_sync", sync), graph=graph)
    process_work_item(MonitorWorkItem("position_sync", sync), graph=graph)

    marker = graph.get_node("MonitorRun", "position-sync:orphan")
    assert marker is not None
    linked = tuple(
        graph.descendants(sync, max_depth=1, edge_types={SNAPSHOT_SYNC_EDGE})
    )
    assert linked == (marker,)
    assert graph.get_node("RunRequest", "run-request:orphan") is None


def test_reconcile_ignores_non_fresh_snapshot() -> None:
    """MON-IDN-02 / MON-STA-02: planted stale snapshot never mutates Positions."""
    graph = InMemoryGraphStore()
    sync = graph.merge_node(
        SNAPSHOT_LABEL,
        "snapshot:stale",
        {"run_id": "stale", "status": "stale", "holdings": ()},
    )

    reconcile_positions_from_snapshot(graph, sync, MonitorSettings())

    assert not graph.list_nodes("Position")
