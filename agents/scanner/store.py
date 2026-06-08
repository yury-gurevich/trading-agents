"""Scanner graph write path.

Agent: scanner
Role: write scanner artifacts and cross-agent provenance into GraphStore.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from contracts.common import Provenance

if TYPE_CHECKING:
    from contracts.scanner import Candidate, FilterTrace
    from kernel import GraphStore, Node


def write_scan(
    graph: GraphStore,
    *,
    universe: str,
    candidates: tuple[Candidate, ...],
    trace: FilterTrace,
    provider_graph_node_id: str | None,
) -> Provenance:
    """Write a scan run, candidate nodes, and provider lineage."""
    run_id = f"scanner-run-{uuid.uuid4().hex}"
    scan = graph.merge_node(
        "ScanRun",
        run_id,
        {
            "universe": universe,
            "candidate_count": len(candidates),
            "universe_size": trace.universe_size,
            "evaluated": trace.evaluated,
            "created_at": datetime.now(tz=UTC).isoformat(),
        },
    )
    for candidate in candidates:
        node = graph.merge_node(
            "Candidate",
            f"{run_id}:{candidate.ticker}",
            {
                "ticker": candidate.ticker,
                "rank": candidate.rank,
                "score": candidate.score,
            },
        )
        graph.add_edge(node, scan, "SURVIVED")
    _add_provider_lineage(graph, scan, provider_graph_node_id)
    return Provenance(
        run_id=run_id,
        source_agent="scanner",
        graph_node_id=f"{scan.label}:{scan.key}",
    )


def _add_provider_lineage(
    graph: GraphStore, scan: Node, provider_graph_node_id: str | None
) -> None:
    if provider_graph_node_id is None or ":" not in provider_graph_node_id:
        return
    label, key = provider_graph_node_id.split(":", 1)
    provider_node = graph.get_node(label, key)
    if provider_node is not None:
        graph.add_edge(scan, provider_node, "DERIVED_FROM")
