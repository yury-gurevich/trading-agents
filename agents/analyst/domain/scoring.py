"""Analyst technical scoring logic.

Agent: analyst
Role: convert candidate market history into technical score and confidence.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.analyst.domain.fundamental_rules import score_fundamental
from agents.analyst.domain.relative_strength import (
    compute_relative_strength,
    score_relative_strength,
)
from agents.analyst.domain.signal_selection import (
    fundamental_signals,
    select_top_signals,
    technical_signals,
)
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
    top_signals: tuple[str, ...] = ()
    rejection_reason: str | None = None


def score_candidate(
    candidate: Candidate,  # noqa: ARG001 - kept for call-site stability; the
    # analyst now scores on its own technical evidence, not the scanner prior.
    bars: tuple[OHLCVBar, ...],
    fundamentals: dict[str, float],
    benchmark_bars: tuple[OHLCVBar, ...],
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
    technical, rs_metrics = _apply_relative_strength(
        _bounded(raw / 100.0), bars, benchmark_bars, settings
    )
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
        **rs_metrics,
    }
    if fundamental is not None:
        metrics["fundamental_score"] = fundamental
    signals = technical_signals(tmetrics) + fundamental_signals(fmetrics)
    selected = select_top_signals(
        signals,
        {
            "technical": settings.technical_weight,
            "fundamental": settings.fundamental_weight,
        },
        slack=settings.signal_diversity_slack,
        max_signals=settings.max_top_signals,
    )
    return ScoreBreakdown(
        technical_score=technical,
        confidence=confidence,
        metrics=metrics,
        fundamental_score=fundamental,
        top_signals=tuple(signal.name for signal in selected),
    )


def _apply_relative_strength(
    technical: float,
    bars: tuple[OHLCVBar, ...],
    benchmark_bars: tuple[OHLCVBar, ...],
    settings: AnalystSettings,
) -> tuple[float, dict[str, float]]:
    """Blend relative strength into the technical pillar (0.8 technical / 0.2 RS).

    Returns the (possibly adjusted) technical score and audit metrics. When the
    benchmark history is insufficient the technical score passes through unchanged.
    """
    raw = compute_relative_strength(bars, benchmark_bars, settings.rs_window)
    if raw is None:
        return technical, {}
    rs_score = score_relative_strength(raw)
    weight = settings.relative_strength_weight
    blended = _bounded((1.0 - weight) * technical + weight * _bounded(rs_score / 100.0))
    return blended, {"relative_strength": raw, "rs_score": rs_score}


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
