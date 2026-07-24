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
    from agents.analyst.domain.sentiment_reading import SentimentReading
    from contracts.analyst import Recommendation, Rejection
    from contracts.scanner import CandidateSet
    from kernel import GraphStore, Node


def write_analysis(
    graph: GraphStore,
    *,
    candidate_set: CandidateSet,
    recommendations: tuple[Recommendation, ...],
    rejections: tuple[Rejection, ...],
    sentiment_readings: tuple[SentimentReading, ...] = (),
    incident_refs: tuple[str, ...] = (),
    held_count: int = 0,
) -> Provenance:
    """Write an analyst run, recommendations, sentiment readings, and lineage."""
    run_id = f"analyst-run-{uuid.uuid4().hex}"
    run = graph.merge_node(
        "AnalystRun",
        run_id,
        {
            "recommendation_count": len(recommendations),
            "rejection_count": len(rejections),
            "held_count": held_count,
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
                "exit_trigger": recommendation.exit_trigger,
                "confidence": recommendation.confidence,
                "technical_score": recommendation.technical_score,
                "quant_metrics": [
                    metric.model_dump(mode="json")
                    for metric in recommendation.quant_metrics
                ],
            },
        )
        _link_candidate(graph, node, scan_key, recommendation.ticker)
    _write_readings(graph, run, run_id, sentiment_readings)
    return Provenance(
        run_id=run_id,
        source_agent="analyst",
        graph_node_id=f"{run.label}:{run.key}",
        incident_refs=incident_refs,
    )


def _write_readings(
    graph: GraphStore,
    run: Node,
    run_id: str,
    readings: tuple[SentimentReading, ...],
) -> None:
    """Persist each scorer's sentiment reading, linked to the run that produced it."""
    for reading in readings:
        node = graph.merge_node(
            "SentimentReading",
            f"{run_id}:{reading.scorer}:{reading.ticker}",
            {
                "ticker": reading.ticker,
                "scorer": reading.scorer,
                "score": reading.score,
                "articles": float(reading.articles),
                "positive": float(reading.positive),
                "negative": float(reading.negative),
                "source_run_id": run_id,
            },
        )
        graph.add_edge(run, node, "PRODUCED")


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
