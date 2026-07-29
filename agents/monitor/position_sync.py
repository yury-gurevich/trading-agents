"""Monitor-owned head-of-run position-book sync marker.

Agent: monitor
Role: adopt execution's broker snapshot and mark the run's book as fresh or stale.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.monitor.reconcile import reconcile_positions_from_snapshot
from agents.monitor.settings import MonitorSettings
from contracts.position_sync import (
    POSITION_SYNC_EDGE,
    POSITION_SYNC_PHASE,
    RUN_REQUEST_LABEL,
    SNAPSHOT_LABEL,
    SNAPSHOT_SYNC_EDGE,
    run_request_key,
)
from kernel import CollectingFaultSink, fault_boundary
from kernel.fault_graph import GraphFaultSink

if TYPE_CHECKING:
    from kernel import FaultSink, GraphStore, Node


def find_pending_position_sync(graph: GraphStore) -> list[Node]:
    """Return run-request snapshots not yet adopted or marked stale by monitor."""
    pending: list[Node] = []
    for node in graph.list_nodes(SNAPSHOT_LABEL):
        run_id = str(node.props.get("run_id", ""))
        if graph.get_node(RUN_REQUEST_LABEL, run_request_key(run_id)) is None:
            continue
        synced = list(
            graph.descendants(node, max_depth=1, edge_types={SNAPSHOT_SYNC_EDGE})
        )
        if not any(_is_sync_marker(item) for item in synced):
            pending.append(node)
    return pending


def sync_positions_snapshot(
    node: Node,
    *,
    graph: GraphStore,
    settings: MonitorSettings | None = None,
    sink: FaultSink | None = None,
) -> None:
    """Adopt one execution-authored snapshot and mark the run as sync-attempted."""
    settings = settings or MonitorSettings()
    sink = sink if sink is not None else GraphFaultSink(graph, CollectingFaultSink())
    status = str(node.props.get("status", "stale"))
    with fault_boundary(
        sink,
        agent="monitor",
        module="agents.monitor.position_sync",
        capability="position_sync",
        reraise=False,
    ):
        if status == "fresh":
            reconcile_positions_from_snapshot(graph, node, settings)
        _write_sync_marker(graph, node, status=status)


def _write_sync_marker(graph: GraphStore, snapshot: Node, *, status: str) -> Node:
    run_id = str(snapshot.props["run_id"])
    key = f"position-sync:{run_id}"
    marker = graph.get_node("MonitorRun", key)
    if marker is not None:
        graph.add_edge(snapshot, marker, SNAPSHOT_SYNC_EDGE)
        request = graph.get_node(RUN_REQUEST_LABEL, run_request_key(run_id))
        if request is not None:
            graph.add_edge(request, marker, POSITION_SYNC_EDGE)
        return marker
    props: dict[str, object] = {
        "source_run_id": run_id,
        "phase": POSITION_SYNC_PHASE,
        "position_book_status": "fresh" if status == "fresh" else "stale",
        "snapshot_key": snapshot.key,
        "positions_checked": 0,
        "closes": 0,
        "holds": 0,
        "stop_breaches": 0,
        "created_at": datetime.now(tz=UTC).isoformat(),
    }
    stale_reason = snapshot.props.get("stale_reason")
    if stale_reason:
        props["position_book_stale_reason"] = str(stale_reason)
    marker = graph.merge_node("MonitorRun", key, props)
    graph.add_edge(snapshot, marker, SNAPSHOT_SYNC_EDGE)
    request = graph.get_node(RUN_REQUEST_LABEL, run_request_key(run_id))
    if request is not None:
        graph.add_edge(request, marker, POSITION_SYNC_EDGE)
    return marker


def _is_sync_marker(node: Node) -> bool:
    return node.label == "MonitorRun" and node.props.get("phase") == POSITION_SYNC_PHASE
