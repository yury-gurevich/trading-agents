"""Reporter graph write path.

Agent: reporter
Role: write reporter-owned Snapshot and TradeNarrative graph artifacts.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.common import Provenance

if TYPE_CHECKING:
    from kernel import GraphStore, Node


def write_snapshot(
    graph: GraphStore,
    *,
    run_id: str,
    metrics_blob: dict[str, dict[str, float]],
    headline_summary: str,
) -> Provenance:
    """Write one run snapshot and link it to the PM run when present."""
    node = graph.merge_node(
        "Snapshot",
        f"snapshot:{run_id}",
        {
            "run_id": run_id,
            "metrics": metrics_blob,
            "headline_summary": headline_summary,
        },
    )
    pm_run = graph.get_node("PMRun", run_id)
    if pm_run is not None:
        graph.add_edge(node, pm_run, "SUMMARISES")
    return _provenance("snapshot", node)


def write_trade_narrative(
    graph: GraphStore,
    *,
    run_id: str,
    position_id: str,
    story: str,
) -> Provenance:
    """Write one trade narrative and link it to the Position when present."""
    node = graph.merge_node(
        "TradeNarrative",
        f"narrative:{position_id}",
        {"run_id": run_id, "position_id": position_id, "summary": story},
    )
    position = graph.get_node("Position", position_id)
    if position is not None:
        graph.add_edge(node, position, "NARRATES")
    return _provenance("narrative", node)


def _provenance(prefix: str, node: Node) -> Provenance:
    return Provenance(
        run_id=f"{prefix}:{node.key}",
        source_agent="reporter",
        graph_node_id=f"{node.label}:{node.key}",
    )
