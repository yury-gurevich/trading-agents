"""Recommendation rationale text from actually scored indicators.

Agent: analyst
Role: render technical-rationale snippets without claiming skipped inputs.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.analyst.history_requirements import momentum_indicator_requirements

if TYPE_CHECKING:
    from agents.analyst.domain.scoring import ScoreBreakdown
    from agents.analyst.settings import AnalystSettings
    from contracts.provider import RegimeContext
    from contracts.scanner import Candidate


def buy_summary(
    candidate: Candidate,
    score: ScoreBreakdown,
    regime: RegimeContext,
    settings: AnalystSettings,
) -> str:
    """Return buy rationale text naming only indicators present in score.metrics."""
    indicators = _scored_indicator_text(score, settings)
    return (
        f"{candidate.ticker} cleared the {regime.label} confidence gate on "
        f"its composite technical score ({indicators})."
    )


def _scored_indicator_text(score: ScoreBreakdown, settings: AnalystSettings) -> str:
    labels = [
        requirement.label
        for requirement in momentum_indicator_requirements(settings)
        if requirement.metric_name in score.metrics
    ]
    if not labels:
        return "available technical inputs"
    if len(labels) == 1:
        return labels[0]
    return f"{', '.join(labels[:-1])}, and {labels[-1]}"
