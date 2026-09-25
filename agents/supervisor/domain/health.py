"""Supervisor health graph queries.

Agent: supervisor
Role: derive live system health from Fault, Flag, and Snapshot graph nodes.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from kernel.fault_incidents import live_fault_incidents

if TYPE_CHECKING:
    from kernel import GraphStore, Node

# The graph-pull chain's edges, RunRequest down to Snapshot. Agents may not import
# orchestration.batch_chain, so the names are repeated here (as agents/operator does).
_CHAIN_EDGES = {
    "INGESTED_BY",
    "SCANNED_BY",
    "ANALYZED_BY",
    "EVALUATED_BY",
    "EXECUTED_BY",
    "MONITORED_BY",
    "REPORTED_BY",
}


class HealthFields(TypedDict):
    """Raw graph-derived health fields used by MasterReport."""

    healthy: bool
    open_incidents: int
    pending_human_flags: int
    last_successful_run: str | None


def compute_health(graph: GraphStore, run_id: str | None) -> HealthFields:
    """Return raw health fields for a MasterReport."""
    del run_id
    flags = graph.list_nodes("Flag")
    resolutions = graph.list_nodes("FlagResolution")
    snapshots = graph.list_nodes("Snapshot")
    open_incidents = len(live_fault_incidents(graph))
    resolved_keys = {_resolution_key(node) for node in resolutions}
    critical_flags = sum(
        1
        for node in flags
        if _resolution_key(node) not in resolved_keys
        and node.props.get("severity") == "critical"
    )
    latest = _latest_snapshot(graph, snapshots)
    return {
        "healthy": open_incidents == 0 and critical_flags == 0,
        "open_incidents": open_incidents,
        "pending_human_flags": critical_flags,
        "last_successful_run": None if latest is None else _run_name(graph, latest),
    }


def _latest_snapshot(graph: GraphStore, snapshots: tuple[Node, ...]) -> Node | None:
    # A graph-pull Snapshot carries no created_at; its run_id is its PMRun's key, and
    # the PMRun's created_at orders it. Ordering by the node key picked a three-week-old
    # verify run on the live spine (DL-225).
    if not snapshots:
        return None
    created = {
        node.key: str(node.props.get("created_at", ""))
        for node in graph.list_nodes("PMRun")
    }
    return max(snapshots, key=lambda node: (_when(node, created), node.key))


def _when(snapshot: Node, pm_created: dict[str, str]) -> str:
    own = snapshot.props.get("created_at")
    return pm_created.get(str(snapshot.props.get("run_id", ""))) or str(own or "")


def _run_name(graph: GraphStore, snapshot: Node) -> str:
    """Name the run a Snapshot reports: its RunRequest's run id, else the node key."""
    upstream = graph.ancestors(
        snapshot, max_depth=len(_CHAIN_EDGES), edge_types=_CHAIN_EDGES
    )
    request = next((node for node in upstream if node.label == "RunRequest"), None)
    run_id = request.props.get("run_id") if request is not None else None
    return str(run_id) if run_id else snapshot.key


def _resolution_key(node: Node) -> tuple[str, str]:
    return (str(node.props.get("subject_ref")), str(node.props.get("severity")))
