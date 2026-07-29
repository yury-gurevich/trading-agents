"""Execution position-sync work-item branch tests.

Agent: execution
Role: prove mixed sync/submit dispatch and fail-open snapshot handling.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import agents.execution.poll as poll
from agents.execution.broker import BrokerPosition
from agents.execution.poll import (
    ExecutionWorkItem,
    find_pending_work,
    process_work_item,
    sync_run_request,
)
from agents.execution.tests.helpers import PositionBroker
from contracts.position_sync import linked_snapshot, run_request_key
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    import pytest


def test_work_items_prioritize_sync_before_submit() -> None:
    """EXEC-TRG-01 / EXEC-IDN-01: sync work is before order submission work."""
    graph = InMemoryGraphStore()
    run = graph.merge_node("RunRequest", run_request_key("mixed"), {"run_id": "mixed"})
    pm = graph.merge_node("PMRun", "pm-run:mixed", {})

    work = find_pending_work(graph)

    assert [(item.kind, item.node) for item in work] == [
        ("position_sync", run),
        ("submit", pm),
    ]


def test_process_work_item_dispatches_both_kinds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """EXEC-TRG-01 / EXEC-IDN-01: planted work items hit both dispatch arms."""
    graph = InMemoryGraphStore()
    run = graph.merge_node("RunRequest", run_request_key("sync"), {"run_id": "sync"})
    pm = graph.merge_node("PMRun", "pm-run:submit", {})
    broker = PositionBroker((BrokerPosition("AAPL", 1, 10000, 10000),))
    seen: dict[str, object] = {}

    def fake_submit(node: object, **kwargs: object) -> None:
        seen["submit_node"] = node
        seen["submit_graph"] = kwargs["graph"]

    monkeypatch.setattr(poll, "execute_pm_node", fake_submit)

    process_work_item(
        ExecutionWorkItem("position_sync", run), graph=graph, broker=broker
    )
    process_work_item(ExecutionWorkItem("submit", pm), graph=graph, broker=broker)

    assert linked_snapshot(graph, run) is not None
    assert seen == {"submit_node": pm, "submit_graph": graph}


def test_sync_run_request_no_snapshot_and_outer_fault_are_fail_open(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """EXEC-FAIL-02 / EXEC-OBS-02: planted reconcile gaps do not raise."""
    graph = InMemoryGraphStore()
    run = graph.merge_node("RunRequest", run_request_key("none"), {"run_id": "none"})
    broker = PositionBroker(())

    monkeypatch.setattr(poll, "reconcile_run_start", lambda *_, **__: None)
    sync_run_request(run, graph=graph, broker=broker)
    assert linked_snapshot(graph, run) is None

    def raise_outer(*_: object, **__: object) -> object:
        raise RuntimeError("outer reconcile failed")

    monkeypatch.setattr(poll, "reconcile_run_start", raise_outer)
    sync_run_request(run, graph=graph, broker=broker)
    assert linked_snapshot(graph, run) is None
    assert len(graph.list_nodes("Fault")) == 1
