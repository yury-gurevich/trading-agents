"""Analyst technical scoring logic.

Agent: analyst
Role: convert candidate market history into technical score and confidence.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

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
    rejection_reason: str | None = None


def score_candidate(
    candidate: Candidate,  # noqa: ARG001 - kept for call-site stability; the
    # analyst now scores on its own technical evidence, not the scanner prior.
    bars: tuple[OHLCVBar, ...],
    settings: AnalystSettings,
) -> ScoreBreakdown:
    """Score one candidate from its close-price history via the technical engine."""
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
    confidence = _bounded(
        settings.confidence_floor + technical * settings.confidence_span
    )
    metrics = {
        "history_bars": float(len(rows)),
        "technical_score": technical,
        "confidence": confidence,
        **tmetrics,
    }
    return ScoreBreakdown(
        technical_score=technical, confidence=confidence, metrics=metrics
    )


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))
