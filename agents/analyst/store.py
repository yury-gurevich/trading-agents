"""Analyst graph write path.

Agent: analyst
Role: write analyst artifacts and candidate provenance lineage into GraphStore.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from contracts.common import Provenance

if TYPE_CHECKING:
    from contracts.analyst import Recommendation, Rejection
    from contracts.scanner import CandidateSet
    from kernel import GraphStore, Node


def write_analysis(
    graph: GraphStore,
    *,
    candidate_set: CandidateSet,
    recommendations: tuple[Recommendation, ...],
    rejections: tuple[Rejection, ...],
    incident_refs: tuple[str, ...] = (),
) -> Provenance:
    """Write an analyst run, recommendations, and candidate lineage."""
    run_id = f"analyst-run-{uuid.uuid4().hex}"
    run = graph.merge_node(
        "AnalystRun",
        run_id,
        {
            "recommendation_count": len(recommendations),
            "rejection_count": len(rejections),
            "source_scan_run_id": candidate_set.run_id,
            "created_at": datetime.now(tz=UTC).isoformat(),
        },
    )
    scan_key = _scan_key(candidate_set)
    for recommendation in recommendations:
        node = graph.merge_node(
            "Recommendation",
            f"{run_id}:{recommendation.ticker}",
            {
                "ticker": recommendation.ticker,
                "action": recommendation.action,
                "confidence": recommendation.confidence,
                "technical_score": recommendation.technical_score,
            },
        )
        _link_candidate(graph, node, scan_key, recommendation.ticker)
    return Provenance(
        run_id=run_id,
        source_agent="analyst",
        graph_node_id=f"{run.label}:{run.key}",
        incident_refs=incident_refs,
    )


def _scan_key(candidate_set: CandidateSet) -> str | None:
    graph_id = candidate_set.provenance.graph_node_id
    if graph_id is None or not graph_id.startswith("ScanRun:"):
        return None
    return graph_id.split(":", 1)[1]


def _link_candidate(
    graph: GraphStore, node: Node, scan_key: str | None, ticker: str
) -> None:
    if scan_key is None:
        return
    candidate = graph.get_node("Candidate", f"{scan_key}:{ticker}")
    if candidate is not None:
        graph.add_edge(node, candidate, "DERIVED_FROM")
