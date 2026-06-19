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
from agents.analyst.domain.sentiment_rules import score_sentiment
from agents.analyst.domain.signal_selection import (
    Signal,
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
    sentiment_score: float | None = None
    alpha158_score: float | None = None
    top_signals: tuple[str, ...] = ()
    rejection_reason: str | None = None


def score_candidate(
    candidate: Candidate,  # noqa: ARG001 - kept for call-site stability; the
    # analyst now scores on its own technical evidence, not the scanner prior.
    bars: tuple[OHLCVBar, ...],
    fundamentals: dict[str, float],
    benchmark_bars: tuple[OHLCVBar, ...],
    news: tuple[str, ...],
    settings: AnalystSettings,
    *,
    alpha_score: float | None = None,
) -> ScoreBreakdown:
    """Score one candidate from price history, fundamentals, and news; then blend."""
    rows = sorted(bars, key=lambda bar: bar.bar_date)
    if len(rows) < settings.min_history_bars:
        return ScoreBreakdown(
            technical_score=0.0,
            confidence=0.0,
            metrics={"history_bars": float(len(rows))},
            alpha158_score=alpha_score,
            rejection_reason="insufficient_market_history",
        )

    raw, tmetrics = score_technical(rows, settings)
    technical, rs_metrics = _apply_relative_strength(
        _bounded(raw / 100.0), bars, benchmark_bars, settings
    )
    raw_fund, fmetrics = score_fundamental(fundamentals)
    fundamental = None if raw_fund is None else _bounded(raw_fund / 100.0)
    raw_sent, smetrics = score_sentiment(news)
    sentiment = None if raw_sent is None else _bounded(raw_sent / 100.0)
    alpha = None if alpha_score is None else _bounded(alpha_score / 100.0)
    composite = _composite(technical, fundamental, sentiment, alpha, settings)
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
        **smetrics,
    }
    if fundamental is not None:
        metrics["fundamental_score"] = fundamental
    if sentiment is not None:
        metrics["sentiment_score"] = sentiment
    if alpha_score is not None:
        metrics["alpha158_score"] = alpha_score
    sentiment_signals = (
        [Signal(name="sentiment", pillar="sentiment", score=raw_sent)]
        if raw_sent is not None
        else []
    )
    signals = (
        technical_signals(tmetrics) + fundamental_signals(fmetrics) + sentiment_signals
    )
    selected = select_top_signals(
        signals,
        {
            "technical": settings.technical_weight,
            "fundamental": settings.fundamental_weight,
            "sentiment": settings.sentiment_weight,
        },
        slack=settings.signal_diversity_slack,
        max_signals=settings.max_top_signals,
    )
    return ScoreBreakdown(
        technical_score=technical,
        confidence=confidence,
        metrics=metrics,
        fundamental_score=fundamental,
        sentiment_score=sentiment,
        alpha158_score=alpha_score,
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
    technical: float,
    fundamental: float | None,
    sentiment: float | None,
    alpha: float | None,
    settings: AnalystSettings,
) -> float:
    """Blend the present pillars, renormalised over their weights.

    Returns the technical score alone when all optional pillars are absent;
    otherwise sums each present pillar's weighted value over the present weights
    (so a two-pillar result is exactly today's technical+fundamental blend).
    """
    if fundamental is None and sentiment is None and alpha is None:
        return technical
    weighted = settings.technical_weight * technical
    weight_sum = settings.technical_weight
    if fundamental is not None:
        weighted += settings.fundamental_weight * fundamental
        weight_sum += settings.fundamental_weight
    if sentiment is not None:
        weighted += settings.sentiment_weight * sentiment
        weight_sum += settings.sentiment_weight
    if alpha is not None:
        weighted += settings.alpha158_pillar_weight * alpha
        weight_sum += settings.alpha158_pillar_weight
    return weighted / weight_sum


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))
