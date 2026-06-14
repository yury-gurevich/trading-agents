"""Analyst domain scoring and recommendation tests.

Agent: analyst
Role: verify the technical engine drives scores, confidence, and decisions.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from agents.analyst.domain.recommend import decide
from agents.analyst.domain.scoring import score_candidate
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
    score = score_candidate(candidate(), _rising_bars(1), AnalystSettings())

    decision = decide(candidate(), score, _regime())

    assert score.rejection_reason == "insufficient_market_history"
    assert decision.recommendation is None
    assert decision.rejection is not None
    assert decision.rejection.reason == "insufficient_market_history"


def test_sufficient_history_scores_from_technical_composite() -> None:
    score = score_candidate(candidate(), _rising_bars(40), AnalystSettings())

    # 40 dipping-ramp bars -> RSI 25, MACD 75, Bollinger 30 | ATR 55, Stochastic 20,
    # Williams 25, Choppiness 50 | OBV 70, RSI-2 20 available (SMA-200, EMA-50 and the
    # golden cross not) -> sum 370 / 9. technical = (370/9)/100; conf = 0.30 + t*0.60.
    technical = (370.0 / 9.0) / 100.0
    assert score.metrics["indicators_available"] == 9.0
    assert score.technical_score == pytest.approx(technical, abs=1e-9)
    assert score.confidence == pytest.approx(0.30 + technical * 0.60, abs=1e-9)


def test_thin_history_is_neutral_technical_score() -> None:
    # Two bars is below every indicator window (RSI-2 alone needs three closes), so the
    # composite fully degrades to neutral 0.5 -> confidence 0.60 (clears the floor).
    score = score_candidate(candidate(), _rising_bars(2), AnalystSettings())

    assert score.metrics["indicators_available"] == 0.0
    assert score.technical_score == pytest.approx(0.5, abs=1e-9)
    assert score.confidence == pytest.approx(0.6, abs=1e-9)


def test_zero_confidence_span_floors_confidence() -> None:
    settings = AnalystSettings(confidence_floor=0.0, confidence_span=0.0)

    score = score_candidate(candidate(), _rising_bars(40), settings)

    assert score.confidence == 0.0
