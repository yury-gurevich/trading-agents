"""Analyst technical scoring logic.

Agent: analyst
Role: convert candidate market history into technical score and confidence.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import TYPE_CHECKING

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
    rejection_reason: str | None = None


def score_candidate(
    candidate: Candidate,
    bars: tuple[OHLCVBar, ...],
    settings: AnalystSettings,
) -> ScoreBreakdown:
    """Score one candidate using scanner prior, momentum, and MA trend."""
    rows = sorted(bars, key=lambda bar: bar.bar_date)
    if len(rows) < settings.min_history_bars:
        return ScoreBreakdown(
            technical_score=0.0,
            confidence=0.0,
            metrics={"history_bars": float(len(rows))},
            rejection_reason="insufficient_market_history",
        )

    momentum = (rows[-1].close - rows[0].close) / rows[0].close
    components = {
        "candidate_component": _bounded(candidate.score / settings.score_scale),
        "momentum_component": _bounded(momentum / settings.score_scale),
        "trend_component": _trend_component(rows, settings),
    }
    technical = _weighted_score(components, settings)
    confidence = _bounded(
        settings.confidence_floor + technical * settings.confidence_span
    )
    metrics = {
        "history_bars": float(len(rows)),
        "momentum": momentum,
        "technical_score": technical,
        "confidence": confidence,
        **components,
    }
    return ScoreBreakdown(
        technical_score=technical, confidence=confidence, metrics=metrics
    )


def _weighted_score(components: dict[str, float], settings: AnalystSettings) -> float:
    weights = {
        "candidate_component": settings.candidate_score_weight,
        "momentum_component": settings.momentum_weight,
        "trend_component": settings.trend_weight,
    }
    denominator = sum(weights.values())
    if denominator == 0:
        return 0.0
    return _bounded(
        sum(components[name] * weight for name, weight in weights.items()) / denominator
    )


def _trend_component(rows: list[OHLCVBar], settings: AnalystSettings) -> float:
    if len(rows) < settings.long_ma_bars:
        return 0.5
    short_rows = rows[-settings.short_ma_bars :]
    long_rows = rows[-settings.long_ma_bars :]
    short_ma = mean(bar.close for bar in short_rows)
    long_ma = mean(bar.close for bar in long_rows)
    trend = (short_ma - long_ma) / long_ma
    return _bounded(0.5 + trend / settings.trend_scale)


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))
