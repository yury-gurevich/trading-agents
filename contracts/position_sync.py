"""Shared graph vocabulary for head-of-run position-book sync.

Agent: contracts
Role: define the read-only marker shape proving a run attempted broker sync.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from kernel import GraphStore, Node

RUN_REQUEST_LABEL = "RunRequest"
SNAPSHOT_LABEL = "BrokerPositionSnapshot"
SYNC_MARKER_LABEL = "MonitorRun"
SNAPSHOT_REFRESH_EDGE = "REFRESHES"
SNAPSHOT_SYNC_EDGE = "MONITORED_BY"
POSITION_SYNC_EDGE = "POSITION_SYNCED_BY"
POSITION_SYNC_PHASE = "sync"
POSITION_BOOK_STALE_INCIDENT = "position_book_stale"

SyncStatus = Literal["fresh", "stale"]


@dataclass(frozen=True)
class PositionBookSyncState:
    """Whether the monitor adopted, or visibly declined, a broker snapshot."""

    status: SyncStatus
    marker: Node
    stale_reason: str | None = None


def run_request_key(run_id: str) -> str:
    """Return the graph key for one dispatcher RunRequest."""
    return f"run-request:{run_id}"


def run_request_id(node: Node) -> str:
    """Read a RunRequest's run id from its props."""
    return str(node.props["run_id"])


def linked_snapshot(graph: GraphStore, run_request: Node) -> Node | None:
    """Return the snapshot execution linked to this RunRequest, if any."""
    return next(
        (
            node
            for node in graph.descendants(
                run_request, max_depth=1, edge_types={SNAPSHOT_REFRESH_EDGE}
            )
            if node.label == SNAPSHOT_LABEL
        ),
        None,
    )


def position_book_sync_state(
    graph: GraphStore, run_id: str
) -> PositionBookSyncState | None:
    """Return the monitor's sync marker for a run, if the attempt is complete."""
    run_request = graph.get_node(RUN_REQUEST_LABEL, run_request_key(run_id))
    if run_request is None:
        return None
    marker = next(
        (
            node
            for node in graph.descendants(
                run_request, max_depth=1, edge_types={POSITION_SYNC_EDGE}
            )
            if node.label == SYNC_MARKER_LABEL
            and node.props.get("phase") == POSITION_SYNC_PHASE
        ),
        None,
    )
    if marker is None:
        return None
    status = marker.props.get("position_book_status")
    if status not in ("fresh", "stale"):
        return None
    reason = marker.props.get("position_book_stale_reason")
    return PositionBookSyncState(
        status=status,
        marker=marker,
        stale_reason=str(reason) if reason else None,
    )


def position_book_sync_attempted(graph: GraphStore, run_id: str) -> bool:
    """Return whether a run has a fresh or stale monitor sync marker."""
    return position_book_sync_state(graph, run_id) is not None
