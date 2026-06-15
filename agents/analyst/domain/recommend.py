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
    summary = (
        f"{candidate.ticker} cleared the {regime.label} confidence "
        "gate on its composite technical score (RSI, MACD, Bollinger, "
        "SMA-200 distance, and EMA crossover)."
    )
    evidence_refs: tuple[str, ...] = (
        "analyst.technical_score",
        "provider.market_data",
        "provider.regime",
    )
    if score.fundamental_score is not None:
        summary += f" and a fundamental score of {score.fundamental_score:.3f}"
        evidence_refs += ("analyst.fundamental_score",)
    evidence_refs += tuple(f"analyst.signal.{name}" for name in score.top_signals)
    return AnalysisDecision(
        recommendation=Recommendation(
            ticker=candidate.ticker,
            action="buy",
            confidence=score.confidence,
            technical_score=score.technical_score,
            fundamental_score=score.fundamental_score,
            suggested_stop_pct=regime.base_stop_loss_pct,
            suggested_target_pct=regime.base_take_profit_pct,
            rationale=Explanation(summary=summary, evidence_refs=evidence_refs),
        ),
        rejection=None,
    )
