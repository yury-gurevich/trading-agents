"""Analyst scoring core shared by the bus and graph-pull paths.

Agent: analyst
Role: given a candidate set plus already-acquired market+regime, score, split, and
      persist the analyst run. Called by the bus handler (`_analyze`) and the
      graph-pull poll path (`analyze_scan_node`) so both stay consistent (DL-08b).
External I/O: none (writes via the injected GraphStore).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.analyst.domain.analyze import score_candidates
from agents.analyst.domain.sentiment_reading import provider_reading
from agents.analyst.held_universe import scoring_universe
from agents.analyst.result import build_empty_result, run_explanation, split_decisions
from agents.analyst.store import write_analysis
from contracts.analyst import RecommendationSet
from contracts.positions import open_position_stop_thresholds
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from agents.analyst.settings import AnalystSettings
    from contracts.positions import OpenPosition, PositionStopThreshold
    from contracts.provider import MarketData, RegimeContext
    from contracts.scanner import CandidateSet
    from kernel import FaultSink, GraphStore


def run_analysis(
    graph: GraphStore,
    candidate_set: CandidateSet,
    market: MarketData,
    regime: RegimeContext,
    settings: AnalystSettings,
    sink: FaultSink,
    *,
    incident_refs: tuple[str, ...] = (),
    held_positions: tuple[OpenPosition, ...] = (),
) -> RecommendationSet:
    """Score candidates against an acquired market+regime and persist the run."""
    held_tickers = tuple(position.ticker for position in held_positions)
    scoring_set = scoring_universe(candidate_set, held_positions)
    if market.quality.used_fallback:
        _record_fault(sink, "provider returned degraded market data")
        return build_empty_result(
            graph,
            scoring_set,
            "provider market data degraded",
            incident_refs or ("market_data_degraded",),
            held_count=len(held_positions),
        )
    if regime.provenance.incident_refs:
        _record_fault(sink, "provider regime data degraded")
        return build_empty_result(
            graph,
            scoring_set,
            "provider regime data degraded",
            incident_refs,
            held_count=len(held_positions),
        )
    held_stops = _held_stop_thresholds(graph, sink)
    if held_stops is None:
        return build_empty_result(
            graph,
            scoring_set,
            "held position stop threshold unavailable",
            held_count=len(held_positions),
        )
    decisions = score_candidates(
        scoring_set,
        market,
        regime,
        market.benchmark,
        settings,
        sink,
        held_tickers,
        held_stops,
    )
    if decisions is None:
        return build_empty_result(
            graph,
            scoring_set,
            "analyst scoring failed",
            held_count=len(held_positions),
        )
    recommendations, rejections = split_decisions(decisions)
    lexicon = tuple(
        d.sentiment_reading for d in decisions if d.sentiment_reading is not None
    )
    provider_readings = tuple(
        provider_reading(c.ticker, market.sentiment[c.ticker])
        for c in scoring_set.candidates
        if c.ticker in market.sentiment
    )
    provenance = write_analysis(
        graph,
        candidate_set=scoring_set,
        recommendations=recommendations,
        rejections=rejections,
        sentiment_readings=lexicon + provider_readings,
        incident_refs=incident_refs,
        held_count=len(held_positions),
    )
    return RecommendationSet(
        run_id=provenance.run_id,
        recommendations=recommendations,
        rejections=rejections,
        explanation=run_explanation(recommendations, rejections, regime),
        provenance=provenance,
    )


def _record_fault(sink: FaultSink, message: str) -> None:
    """Record a degraded-provider fault without interrupting analysis."""
    with fault_boundary(
        sink,
        agent="analyst",
        module="agents.analyst.run",
        capability="analyze",
        reraise=False,
    ):
        raise RuntimeError(message)


def _held_stop_thresholds(
    graph: GraphStore, sink: FaultSink
) -> tuple[PositionStopThreshold, ...] | None:
    """Return held stop thresholds, recording non-representable books as faults."""
    thresholds: tuple[PositionStopThreshold, ...] = ()
    with fault_boundary(
        sink,
        agent="analyst",
        module="agents.analyst.run",
        capability="analyze",
        reraise=False,
    ) as capture:
        thresholds = open_position_stop_thresholds(graph)
    return None if capture.fault is not None else thresholds
