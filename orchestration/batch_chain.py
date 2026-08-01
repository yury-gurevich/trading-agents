"""Run-chain traversal shared by trace, acceptance, and resume placement.

Agent: orchestration
Role: read the graph-pull stage chain, including the head position-sync side branch.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.position_sync import POSITION_SYNC_EDGE, POSITION_SYNC_PHASE

if TYPE_CHECKING:
    from kernel import GraphStore, Node

POSITION_SYNC_KEY = "PositionSync"

CHAIN = (
    ("INGESTED_BY", "MarketData"),
    ("SCANNED_BY", "ScanRun"),
    ("ANALYZED_BY", "AnalystRun"),
    ("EVALUATED_BY", "PMRun"),
    ("EXECUTED_BY", "ExecutionRun"),
    ("MONITORED_BY", "MonitorRun"),
    ("REPORTED_BY", "Snapshot"),
)
DELIBERATION_EDGE = "DELIBERATED_BY"
DELIBERATION_KEY = "DeliberationRun"


def walk_chain(graph: GraphStore, run_id: str) -> dict[str, Node]:
    """Walk one run and return found nodes keyed by stage artifact."""
    run_request = graph.get_node("RunRequest", f"run-request:{run_id}")
    if run_request is None:
        return {}
    nodes: dict[str, Node] = {"RunRequest": run_request}
    sync = _position_sync_marker(graph, run_request)
    if sync is not None:
        nodes[POSITION_SYNC_KEY] = sync
    current: Node = run_request
    for edge, label in CHAIN:
        child = next(
            iter(graph.descendants(current, max_depth=1, edge_types={edge})), None
        )
        if child is None:
            break
        nodes[label] = child
        if label == "PMRun":
            deliberation = _deliberation_marker(graph, child)
            if deliberation is not None:
                nodes[DELIBERATION_KEY] = deliberation
        current = child
    return nodes


def _position_sync_marker(graph: GraphStore, run_request: Node) -> Node | None:
    return next(
        (
            node
            for node in graph.descendants(
                run_request, max_depth=1, edge_types={POSITION_SYNC_EDGE}
            )
            if node.label == "MonitorRun"
            and node.props.get("phase") == POSITION_SYNC_PHASE
        ),
        None,
    )


def _deliberation_marker(graph: GraphStore, pm_run: Node) -> Node | None:
    return next(
        iter(graph.descendants(pm_run, max_depth=1, edge_types={DELIBERATION_EDGE})),
        None,
    )
