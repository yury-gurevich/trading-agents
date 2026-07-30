"""Analyst recommendation decision logic.

Agent: analyst
Role: gate scored candidates into recommendations or explainable rejections.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from agents.analyst.domain.recommend_text import held_recommendation_context
from agents.analyst.domain.sentiment_reading import SentimentReading, lexicon_reading
from agents.analyst.domain.stop_target import resolve_stop_target
from contracts.analyst import QuantMetric, Recommendation, Rejection
from contracts.common import Action, Explanation

if TYPE_CHECKING:
    from agents.analyst.domain.scoring import ScoreBreakdown
    from agents.analyst.settings import AnalystSettings
    from contracts.provider import RegimeContext
    from contracts.scanner import Candidate

ExitTrigger = Literal["stop", "thesis"]


@dataclass(frozen=True)
class AnalysisDecision:
    """Recommendation or rejection for one candidate, with its sentiment reading."""

    recommendation: Recommendation | None
    rejection: Rejection | None
    sentiment_reading: SentimentReading | None = None


def decide(
    candidate: Candidate,
    score: ScoreBreakdown,
    regime: RegimeContext,
    *,
    held: bool = False,
    exit_confidence_floor: float = 0.0,
    stop_breached: bool = False,
    settings: AnalystSettings | None = None,
) -> AnalysisDecision:
    """Turn one score into an actionable recommendation or a rejection."""
    settings = _settings(settings)
    reading = lexicon_reading(candidate.ticker, score)
    if held and stop_breached:
        return AnalysisDecision(
            recommendation=_recommendation(
                candidate,
                score,
                regime,
                "sell",
                exit_confidence_floor,
                "stop",
                settings,
            ),
            rejection=None,
            sentiment_reading=reading,
        )
    if score.rejection_reason is not None:
        return AnalysisDecision(
            recommendation=None,
            rejection=Rejection(ticker=candidate.ticker, reason=score.rejection_reason),
            sentiment_reading=reading,
        )
    if held:
        action: Action = "sell" if score.confidence < exit_confidence_floor else "hold"
        exit_trigger: ExitTrigger | None = "thesis" if action == "sell" else None
        return AnalysisDecision(
            recommendation=_recommendation(
                candidate,
                score,
                regime,
                action,
                exit_confidence_floor,
                exit_trigger,
                settings,
            ),
            rejection=None,
            sentiment_reading=reading,
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
            sentiment_reading=reading,
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
    if score.sentiment_score is not None:
        summary += f" and a news-sentiment score of {score.sentiment_score:.3f}"
        evidence_refs += ("analyst.sentiment_score",)
    evidence_refs += tuple(f"analyst.signal.{name}" for name in score.top_signals)
    return AnalysisDecision(
        recommendation=_build_recommendation(
            candidate,
            score,
            "buy",
            regime,
            summary,
            evidence_refs,
            settings,
        ),
        rejection=None,
        sentiment_reading=reading,
    )


def _recommendation(
    candidate: Candidate,
    score: ScoreBreakdown,
    regime: RegimeContext,
    action: Action,
    exit_floor: float,
    exit_trigger: ExitTrigger | None,
    settings: AnalystSettings,
) -> Recommendation:
    summary, evidence_refs = held_recommendation_context(
        candidate.ticker, score.confidence, exit_floor, exit_trigger
    )
    return _build_recommendation(
        candidate,
        score,
        action,
        regime,
        summary,
        evidence_refs,
        exit_trigger=exit_trigger,
        settings=settings,
    )


def _build_recommendation(
    candidate: Candidate,
    score: ScoreBreakdown,
    action: Action,
    regime: RegimeContext,
    summary: str,
    evidence_refs: tuple[str, ...],
    settings: AnalystSettings,
    exit_trigger: ExitTrigger | None = None,
) -> Recommendation:
    stop_target = None
    if action == "buy":
        stop_target = resolve_stop_target(regime, score.metrics, settings)
    return Recommendation(
        ticker=candidate.ticker,
        action=action,
        exit_trigger=exit_trigger,
        confidence=score.confidence,
        technical_score=score.technical_score,
        fundamental_score=score.fundamental_score,
        sentiment_score=score.sentiment_score,
        suggested_stop_pct=None if stop_target is None else stop_target.stop_pct,
        suggested_target_pct=None if stop_target is None else stop_target.target_pct,
        quant_metrics=_quant_metrics(score),
        stop_target_evidence=None if stop_target is None else stop_target.evidence,
        rationale=Explanation(summary=summary, evidence_refs=evidence_refs),
    )


def _quant_metrics(score: ScoreBreakdown) -> tuple[QuantMetric, ...]:
    """Return the full score metric payload in a stable, typed order."""
    return tuple(
        QuantMetric(name=name, value=value)
        for name, value in sorted(score.metrics.items())
    )


def _settings(settings: AnalystSettings | None) -> AnalystSettings:
    if settings is not None:
        return settings
    from agents.analyst.settings import AnalystSettings

    return AnalystSettings()
