"""Analyst recommendation decision logic.

Agent: analyst
Role: gate scored candidates into recommendations or explainable rejections.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from contracts.analyst import Recommendation, Rejection
from contracts.common import Explanation

if TYPE_CHECKING:
    from agents.analyst.domain.scoring import ScoreBreakdown
    from contracts.provider import RegimeContext
    from contracts.scanner import Candidate


@dataclass(frozen=True)
class AnalysisDecision:
    """Recommendation or rejection for one candidate."""

    recommendation: Recommendation | None
    rejection: Rejection | None


def decide(
    candidate: Candidate,
    score: ScoreBreakdown,
    regime: RegimeContext,
) -> AnalysisDecision:
    """Turn one score into an actionable recommendation or a rejection."""
    if score.rejection_reason is not None:
        return AnalysisDecision(
            recommendation=None,
            rejection=Rejection(ticker=candidate.ticker, reason=score.rejection_reason),
        )
    if score.confidence < regime.base_min_confidence:
        return AnalysisDecision(
            recommendation=None,
            rejection=Rejection(
                ticker=candidate.ticker,
                reason=(
                    f"confidence {score.confidence:.3f} below regime floor "
                    f"{regime.base_min_confidence:.3f}"
                ),
            ),
        )
    return AnalysisDecision(
        recommendation=Recommendation(
            ticker=candidate.ticker,
            action="buy",
            confidence=score.confidence,
            technical_score=score.technical_score,
            suggested_stop_pct=regime.base_stop_loss_pct,
            suggested_target_pct=regime.base_take_profit_pct,
            rationale=Explanation(
                summary=(
                    f"{candidate.ticker} cleared the {regime.label} confidence "
                    "gate using scanner strength, momentum, and trend."
                ),
                evidence_refs=(
                    "scanner.candidate",
                    "provider.market_data",
                    "provider.regime",
                ),
            ),
        ),
        rejection=None,
    )
