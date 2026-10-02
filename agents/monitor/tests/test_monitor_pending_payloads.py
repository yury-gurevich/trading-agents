"""S252 A4: monitor sync discovers requests, reads their snapshots and repairs markers.

Agent: monitor
Role: prove no orphan-snapshot payload is fetched, request order and both decided
      set differences.
External I/O: none (in-memory graph).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.poll_payload_remaining import seed_monitor_sync
from tests.poll_payload_support import PayloadSpy

from agents.monitor.position_sync import (
    find_pending_position_sync,
    sync_positions_snapshot,
)
from contracts.position_sync import (
    POSITION_SYNC_EDGE,
    RUN_REQUEST_LABEL,
    SNAPSHOT_LABEL,
    SNAPSHOT_SYNC_EDGE,
)
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from collections.abc import Iterator

    from kernel import Node


class SnapshotPayloadSpy(PayloadSpy):
    """Keep the original refusal checks and also track every snapshot payload read."""

    def __init__(self) -> None:
        super().__init__()
        self.snapshots: list[str] = []

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        if self.label:
            assert label != SNAPSHOT_LABEL, "sync poll listed every snapshot with props"
        return super().list_nodes(label)

    def get_node(self, label: str, key: str) -> Node | None:
        if self.label and label == SNAPSHOT_LABEL:
            self.snapshots.append(key)
        return super().get_node(label, key)

    def descendants(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        for item in super().descendants(
            node, max_depth=max_depth, edge_types=edge_types
        ):
            if self.label and item.label == SNAPSHOT_LABEL:
                self.snapshots.append(item.key)
            yield item


def test_monitor_sync_fetches_only_linked_snapshots_in_request_order() -> None:
    """MON-TRG-02: a/c snapshots follow c/a requests; done/unwritten and 106 PM
    orphans stay unread.
    """
    graph = SnapshotPayloadSpy()
    seed_monitor_sync(graph)
    graph.arm(RUN_REQUEST_LABEL, POSITION_SYNC_EDGE)

    found = find_pending_position_sync(graph)

    assert graph.snapshots == ["snapshot:c", "snapshot:a", "snapshot:half"]
    assert graph.fetched == [
        "run-request:c",
        "run-request:a",
        "run-request:awaiting",
        "run-request:half",
    ]
    assert [node.key for node in found] == ["snapshot:c", "snapshot:a", "snapshot:half"]


def test_a_half_written_sync_marker_is_reselected_and_completed_once() -> None:
    """MON-TRG-02 / MON-STA-02: retry keeps one marker and completes both edges
    without rewriting it.
    """
    graph = InMemoryGraphStore()
    request = graph.merge_node(
        RUN_REQUEST_LABEL, "run-request:half", {"run_id": "half"}
    )
    snapshot = graph.merge_node(
        SNAPSHOT_LABEL, "snapshot:half", {"run_id": "half", "status": "stale"}
    )
    graph.add_edge(request, snapshot, "REFRESHES")
    marker = graph.merge_node(
        "MonitorRun",
        "position-sync:half",
        {"phase": "sync", "position_book_status": "stale"},
    )
    graph.add_edge(snapshot, marker, SNAPSHOT_SYNC_EDGE)
    before = dict(marker.props)

    assert find_pending_position_sync(graph) == [snapshot]
    sync_positions_snapshot(snapshot, graph=graph)
    sync_positions_snapshot(snapshot, graph=graph)

    assert graph.list_nodes("MonitorRun") == (marker,)
    assert dict(marker.props) == before
    assert tuple(
        graph.descendants(request, max_depth=1, edge_types={POSITION_SYNC_EDGE})
    ) == (marker,)
    assert tuple(
        graph.descendants(snapshot, max_depth=1, edge_types={SNAPSHOT_SYNC_EDGE})
    ) == (marker,)
    assert find_pending_position_sync(graph) == []


def test_a_second_snapshot_of_an_already_synced_request_is_not_picked_up() -> None:
    """MON-TRG-02: decision 3 intentionally excludes a later snapshot of a synced
    run.
    """
    graph = PayloadSpy()
    request = graph.merge_node(
        RUN_REQUEST_LABEL, "run-request:done", {"run_id": "done"}
    )
    marker = graph.merge_node("MonitorRun", "position-sync:done", {"phase": "sync"})
    graph.add_edge(request, marker, POSITION_SYNC_EDGE)
    later = graph.merge_node(
        SNAPSHOT_LABEL, "snapshot:second", {"run_id": "done", "status": "stale"}
    )
    graph.add_edge(request, later, "REFRESHES")
    graph.arm(RUN_REQUEST_LABEL, POSITION_SYNC_EDGE)

    assert find_pending_position_sync(graph) == []
    assert graph.fetched == []
