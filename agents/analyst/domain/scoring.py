"""Analyst technical scoring logic.

Agent: analyst
Role: convert candidate market history into technical score and confidence.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.analyst.domain.fundamental_rules import score_fundamental
from agents.analyst.domain.technical_rules import score_technical

if TYPE_CHECKING:
    from agents.analyst.settings import AnalystSettings
    from contracts.provider import OHLCVBar
    from contracts.scanner import Candidate


@dataclass(frozen=True)
class ScoreBreakdown:
    """Technical scoring output for one candidate."""

    technical_score: float
    confidence: float
    metrics: dict[str, float]
    fundamental_score: float | None = None
    rejection_reason: str | None = None


def score_candidate(
    candidate: Candidate,  # noqa: ARG001 - kept for call-site stability; the
    # analyst now scores on its own technical evidence, not the scanner prior.
    bars: tuple[OHLCVBar, ...],
    fundamentals: dict[str, float],
    settings: AnalystSettings,
) -> ScoreBreakdown:
    """Score one candidate from its price history and fundamentals, then blend."""
    rows = sorted(bars, key=lambda bar: bar.bar_date)
    if len(rows) < settings.min_history_bars:
        return ScoreBreakdown(
            technical_score=0.0,
            confidence=0.0,
            metrics={"history_bars": float(len(rows))},
            rejection_reason="insufficient_market_history",
        )

    raw, tmetrics = score_technical(rows, settings)
    technical = _bounded(raw / 100.0)
    raw_fund, fmetrics = score_fundamental(fundamentals)
    fundamental = None if raw_fund is None else _bounded(raw_fund / 100.0)
    composite = _composite(technical, fundamental, settings)
    confidence = _bounded(
        settings.confidence_floor + composite * settings.confidence_span
    )
    metrics = {
        "history_bars": float(len(rows)),
        "technical_score": technical,
        "composite_score": composite,
        "confidence": confidence,
        **tmetrics,
        **fmetrics,
    }
    if fundamental is not None:
        metrics["fundamental_score"] = fundamental
    return ScoreBreakdown(
        technical_score=technical,
        confidence=confidence,
        metrics=metrics,
        fundamental_score=fundamental,
    )


def _composite(
    technical: float, fundamental: float | None, settings: AnalystSettings
) -> float:
    """Blend the present pillars, renormalised over their weights.

    Returns the technical score alone when no fundamental pillar is available.
    """
    if fundamental is None:
        return technical
    weight_t, weight_f = settings.technical_weight, settings.fundamental_weight
    return (weight_t * technical + weight_f * fundamental) / (weight_t + weight_f)


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))
