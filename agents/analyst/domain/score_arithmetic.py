"""Capture the arithmetic used by one analyst score without changing it.

Agent: analyst
Role: record settings and the ordered names of the sub-scores actually averaged.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.analyst import ScoreArithmetic

if TYPE_CHECKING:
    from agents.analyst.settings import AnalystSettings


def record_arithmetic(
    settings: AnalystSettings,
    technical_metrics: dict[str, float],
    fundamental_metrics: dict[str, float],
) -> ScoreArithmetic:
    """Capture each pillar's metrics before the combined payload is sorted."""
    return ScoreArithmetic(
        technical_weight=settings.technical_weight,
        fundamental_weight=settings.fundamental_weight,
        sentiment_weight=settings.sentiment_weight,
        alpha158_weight=settings.alpha158_pillar_weight,
        relative_strength_weight=settings.relative_strength_weight,
        confidence_floor=settings.confidence_floor,
        confidence_span=settings.confidence_span,
        technical_sub_scores=tuple(
            name for name in technical_metrics if name.endswith("_score")
        ),
        fundamental_sub_scores=tuple(
            name for name in fundamental_metrics if name != "fundamentals_available"
        ),
    )
