"""The broker snapshot a PM run weighs its held book at (PM-IN-05, DL-242).

Agent: portfolio_manager
Role: pick the run's own BrokerPositionSnapshot, or the one of the run it resumes.
External I/O: none (reads the injected GraphStore).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from kernel import GraphStore, Node

SNAPSHOT_LABEL = "BrokerPositionSnapshot"
_RUN_REQUEST_LABEL = "RunRequest"

# Each hop is an operator's resume of a stalled run, and there are eight resumable
# stages: a session resumed eight times over is past any recovery the fleet has
# needed. The bound only ends a lineage that loops, which the graph should never hold.
MAX_RESUME_HOPS = 8


def run_snapshot(graph: GraphStore, run_id: str | None) -> Node | None:
    """Return the latest snapshot of ``run_id``, else of the nearest run it resumes.

    With no ``run_id`` (the RPC path) it is the latest snapshot of all runs. A run
    with no snapshot of its own follows ``RunRequest.source_run_id`` at most
    ``MAX_RESUME_HOPS`` times; ``None`` means no run in the lineage has one.
    """
    snapshots = graph.list_nodes(SNAPSHOT_LABEL)
    if run_id is None:
        return _latest(snapshots)
    by_run: dict[str, list[Node]] = {}
    for node in snapshots:
        by_run.setdefault(str(node.props.get("run_id", "")), []).append(node)
    current: str | None = run_id
    for _hop in range(MAX_RESUME_HOPS + 1):
        if current is None:
            return None
        found = _latest(by_run.get(current, ()))
        if found is not None:
            return found
        current = _source_run_id(graph, current)
    return None


def _source_run_id(graph: GraphStore, run_id: str) -> str | None:
    request = graph.get_node(_RUN_REQUEST_LABEL, f"run-request:{run_id}")
    if request is None:
        return None
    source = request.props.get("source_run_id")
    return str(source) if source else None


def _latest(snapshots: Iterable[Node]) -> Node | None:
    return max(
        snapshots, key=lambda node: str(node.props.get("created_at", "")), default=None
    )
