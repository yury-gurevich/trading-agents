"""Analyst domain scoring and recommendation tests.

Agent: analyst
Role: verify the technical engine drives scores, confidence, and decisions.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from agents.analyst.domain.recommend import decide
from agents.analyst.domain.scoring import ScoreBreakdown, score_candidate
from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import candidate
from contracts.common import Provenance
from contracts.provider import OHLCVBar, RegimeContext


def _regime(floor: float = 0.6) -> RegimeContext:
    return RegimeContext(
        label="risk_on",
        vix=12.0,
        as_of=datetime.now(tz=UTC),
        base_min_confidence=floor,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="regime-fixture", source_agent="provider"),
    )


def _rising_bars(count: int) -> tuple[OHLCVBar, ...]:
    # A rising trend that dips every 5th bar with cycling volume, so the volume/event
    # indicators (OBV in particular) see genuine up *and* down steps, not a monotone.
    base = date(2025, 1, 1)
    bars = []
    for offset in range(count):
        close = 100.0 + offset - (2.0 if (offset % 5 == 0 and offset > 0) else 0.0)
        bars.append(
            OHLCVBar(
                ticker="AAPL",
                bar_date=base + timedelta(days=offset),
                open=close,
                high=close + 2.0,
                low=close - 2.0,
                close=close,
                volume=1_000_000 + (offset % 3) * 250_000,
            )
        )
    return tuple(bars)


def test_score_candidate_reports_insufficient_history() -> None:
    """Kills agents.analyst.domain.scoring.x_score_candidate__mutmut_8."""
    score = score_candidate(candidate(), _rising_bars(1), {}, (), (), AnalystSettings())

    decision = decide(candidate(), score, _regime())

    assert score.rejection_reason == "insufficient_market_history"
    assert score.technical_score == 0.0
    assert score.confidence == 0.0
    assert score.metrics == {"history_bars": 1.0}
    assert decision.recommendation is None
    assert decision.rejection is not None
    assert decision.rejection.reason == "insufficient_market_history"


def test_sufficient_history_scores_from_technical_composite() -> None:
    score = score_candidate(
        candidate(), _rising_bars(40), {}, (), (), AnalystSettings()
    )

    # 40 dipping-ramp bars -> RSI 25, MACD 75, Bollinger 30 | ATR 55, Stochastic 20,
    # Williams 25, Choppiness 50 | OBV 70, RSI-2 20 | NW +4.82% -> 30, turnaround (last
    # bar Sun) -> 50 available (SMA-200, EMA-50, golden cross and any pattern not) ->
    # sum 450 / 11. technical = (450/11)/100; conf = 0.30 + t*0.60.
    technical = (450.0 / 11.0) / 100.0
    assert score.metrics["indicators_available"] == 11.0
    assert (
        score.metrics["technical_score"]
        == score.technical_score
        == pytest.approx(technical, abs=1e-9)
    )
    assert score.confidence == pytest.approx(0.30 + technical * 0.60, abs=1e-9)


def test_thin_history_is_neutral_technical_score() -> None:
    # Two bars is below every indicator window (RSI-2 alone needs three closes), so the
    # composite fully degrades to neutral 0.5 -> confidence 0.60 (clears the floor).
    score = score_candidate(candidate(), _rising_bars(2), {}, (), (), AnalystSettings())

    assert score.metrics["indicators_available"] == 0.0
    assert score.technical_score == pytest.approx(0.5, abs=1e-9)
    assert score.confidence == pytest.approx(0.6, abs=1e-9)


@pytest.mark.parametrize(
    ("confidence", "recommended"),
    [(0.599, False), (0.6, True), (0.601, True)],
)
def test_decide_closed_confidence_floor(confidence: float, recommended: bool) -> None:
    """Kills agents.analyst.domain.recommend.x_decide__mutmut_16."""
    score = ScoreBreakdown(technical_score=0.5, confidence=confidence, metrics={})
    decision = decide(candidate(), score, _regime(floor=0.6))

    assert (decision.recommendation is not None) is recommended
    assert (decision.rejection is None) is recommended


def test_fundamentals_blend_into_confidence_and_recommendation() -> None:
    # Same 40-bar technical (450/11/100). Two fundamentals: peTTM 8 -> <10 -> 80,
    # roeTTM 20 -> >15 -> 80; mean 80 -> fundamental 0.80. composite renormalises over
    # the 0.50/0.30 weights; confidence = floor + composite*span.
    settings = AnalystSettings()
    fundamentals = {"peTTM": 8.0, "roeTTM": 20.0}
    technical = (450.0 / 11.0) / 100.0
    fundamental = 0.80
    composite = (
        settings.technical_weight * technical
        + settings.fundamental_weight * fundamental
    ) / (settings.technical_weight + settings.fundamental_weight)
    expected = settings.confidence_floor + composite * settings.confidence_span

    score = score_candidate(
        candidate(), _rising_bars(40), fundamentals, (), (), settings
    )
    decision = decide(candidate(), score, _regime(floor=0.3))

    assert score.technical_score == pytest.approx(technical, abs=1e-9)
    assert score.fundamental_score == pytest.approx(fundamental, abs=1e-9)
    assert score.metrics["composite_score"] == pytest.approx(composite, abs=1e-9)
    assert score.metrics["fundamental_score"] == pytest.approx(fundamental, abs=1e-9)
    assert score.metrics["fundamentals_available"] == 2.0
    assert score.confidence == pytest.approx(expected, abs=1e-9)
    assert decision.recommendation is not None
    rec = decision.recommendation
    assert rec.fundamental_score == pytest.approx(fundamental, abs=1e-9)
    assert "fundamental score of" in rec.rationale.summary
    assert "analyst.fundamental_score" in rec.rationale.evidence_refs


def test_zero_confidence_span_floors_confidence() -> None:
    settings = AnalystSettings(confidence_floor=0.0, confidence_span=0.0)

    score = score_candidate(candidate(), _rising_bars(40), {}, (), (), settings)

    assert score.confidence == 0.0


def test_sentiment_blends_three_pillars_into_confidence() -> None:
    # Same 40-bar technical (450/11/100) + fundamentals -> 0.80 + an all-positive
    # headline -> 1.0. composite renormalises over the 0.50/0.30/0.20 weights.
    settings = AnalystSettings()
    fundamentals = {"peTTM": 8.0, "roeTTM": 20.0}
    news = ("Apple beats estimates and profit surges to record",)
    technical = (450.0 / 11.0) / 100.0
    composite = (
        settings.technical_weight * technical
        + settings.fundamental_weight * 0.80
        + settings.sentiment_weight * 1.0
    ) / (
        settings.technical_weight
        + settings.fundamental_weight
        + settings.sentiment_weight
    )
    expected = settings.confidence_floor + composite * settings.confidence_span

    score = score_candidate(
        candidate(), _rising_bars(40), fundamentals, (), news, settings
    )
    decision = decide(candidate(), score, _regime(floor=0.3))

    assert score.sentiment_score == pytest.approx(1.0, abs=1e-9)
    assert score.metrics["sentiment_score"] == pytest.approx(1.0, abs=1e-9)
    assert score.metrics["fundamental_score"] == pytest.approx(0.80, abs=1e-9)
    assert score.metrics["sentiment_articles"] == 1.0
    assert score.metrics["sentiment_positive"] == 4.0
    assert score.confidence == pytest.approx(expected, abs=1e-9)
    assert decision.recommendation is not None
    rec = decision.recommendation
    assert rec.sentiment_score == pytest.approx(1.0, abs=1e-9)
    assert "news-sentiment score of" in rec.rationale.summary
    assert "analyst.sentiment_score" in rec.rationale.evidence_refs
    assert "analyst.signal.sentiment" in rec.rationale.evidence_refs
    assert score.top_signals == ("stochastic_k", "sentiment", "rsi2", "pe", "rsi")


def test_sentiment_without_fundamentals_two_pillar_blend() -> None:
    """Kills agents.analyst.domain.scoring.x_score_candidate__mutmut_54."""
    settings = AnalystSettings()
    news = ("Shares report profit and loss",)
    score = score_candidate(candidate(), _rising_bars(40), {}, (), news, settings)

    assert score.sentiment_score == pytest.approx(0.5, abs=1e-9)
    assert score.metrics["sentiment_negative"] == 1.0
    assert score.confidence == pytest.approx(0.561038961038961, abs=1e-9)
