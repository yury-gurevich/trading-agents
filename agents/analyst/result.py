"""Analyst response assembly helpers.

Agent: analyst
Role: build RecommendationSet payloads and run-level explanations.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.analyst.store import write_analysis
from contracts.analyst import Recommendation, RecommendationSet, Rejection
from contracts.common import Explanation

if TYPE_CHECKING:
    from agents.analyst.domain.recommend import AnalysisDecision
    from contracts.provider import MarketData, RegimeContext
    from contracts.scanner import CandidateSet
    from kernel import GraphStore


def build_empty_result(
    graph: GraphStore,
    candidate_set: CandidateSet,
    reason: str,
    incident_refs: tuple[str, ...] = (),
) -> RecommendationSet:
    """Build an explainable no-recommendation result."""
    rejections = tuple(
        Rejection(ticker=candidate.ticker, reason=reason)
        for candidate in candidate_set.candidates
    )
    provenance = write_analysis(
        graph,
        candidate_set=candidate_set,
        recommendations=(),
        rejections=rejections,
        incident_refs=incident_refs,
    )
    return RecommendationSet(
        run_id=provenance.run_id,
        recommendations=(),
        rejections=rejections,
        explanation=Explanation(
            summary=f"No recommendations: {reason}.",
            evidence_refs=("analyst.technical_score",),
        ),
        provenance=provenance,
    )


def split_decisions(
    decisions: tuple[AnalysisDecision, ...],
) -> tuple[tuple[Recommendation, ...], tuple[Rejection, ...]]:
    """Split per-candidate decisions into response tuples."""
    recommendations: list[Recommendation] = []
    rejections: list[Rejection] = []
    for decision in decisions:
        if decision.recommendation is not None:
            recommendations.append(decision.recommendation)
        if decision.rejection is not None:
            rejections.append(decision.rejection)
    return tuple(recommendations), tuple(rejections)


def run_explanation(
    recommendations: tuple[Recommendation, ...],
    rejections: tuple[Rejection, ...],
    regime: RegimeContext,
) -> Explanation:
    """Build the run-level explanation."""
    if not recommendations:
        return Explanation(
            summary=(
                f"No candidates cleared the {regime.label} confidence floor; "
                f"{len(rejections)} were rejected with reasons."
            ),
            evidence_refs=("analyst.technical_score", "provider.regime"),
        )
    return Explanation(
        summary=(
            f"{len(recommendations)} recommendations cleared the {regime.label} "
            f"confidence floor; {len(rejections)} candidates were rejected."
        ),
        evidence_refs=("analyst.technical_score", "provider.regime"),
    )


def incident_refs(
    market: MarketData | None, regime: RegimeContext | None
) -> tuple[str, ...]:
    """Combine incident refs from provider payloads without duplicates."""
    refs: list[str] = []
    if market is not None:
        refs.extend(market.provenance.incident_refs)
    if regime is not None:
        refs.extend(regime.provenance.incident_refs)
    return tuple(dict.fromkeys(refs))
