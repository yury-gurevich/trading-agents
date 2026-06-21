"""Reporter graph-poll work source (DL-08 / DL-08b).

Agent: reporter
Role: find MonitorRun nodes the reporter has not summarised yet and build their run
      snapshot straight from the graph — `build_snapshot` is already fully graph-native,
      so this only adds the poll trigger and the processed edge (no bus RPC).
External I/O: none (reads/writes the injected GraphStore).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.reporter.result import build_snapshot

if TYPE_CHECKING:
    from kernel import GraphStore, Node

MONITOR_RUN_LABEL = "MonitorRun"
REPORTED_EDGE = "REPORTED_BY"


def find_pending(graph: GraphStore) -> list[Node]:
    """Return MonitorRun nodes with no downstream Snapshot (unprocessed work)."""
    pending: list[Node] = []
    for node in graph.list_nodes(MONITOR_RUN_LABEL):
        reported = list(
            graph.descendants(node, max_depth=1, edge_types={REPORTED_EDGE})
        )
        if not reported:
            pending.append(node)
    return pending


def report_monitor_node(node: Node, *, graph: GraphStore) -> None:
    """Build one MonitorRun's snapshot from the graph and link it back."""
    pm_run_id = str(node.props["source_run_id"])
    build_snapshot(graph, pm_run_id)
    snapshot = graph.get_node("Snapshot", f"snapshot:{pm_run_id}")
    assert snapshot is not None  # build_snapshot always writes the Snapshot node.
    graph.add_edge(node, snapshot, REPORTED_EDGE)
