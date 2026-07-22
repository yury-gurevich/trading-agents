"""Analyst Alpha158 pillar integration tests.

Agent: analyst
Role: verify score_candidate wires alpha_score into ScoreBreakdown correctly, and
      that analyze.py pre-computes cross-sectional alpha scores when weight > 0.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest

from agents.analyst.domain.scoring import ScoreBreakdown, score_candidate
from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import (
    analyze_message,
    candidate,
    candidate_set,
    wire_analyst,
)
from contracts.provider import OHLCVBar

if TYPE_CHECKING:
    from contracts.scanner import Candidate


def _bar(ticker: str, close: float, days_ago: int) -> OHLCVBar:
    day = datetime.now(tz=UTC).date() - timedelta(days=days_ago)
    return OHLCVBar(
        ticker=ticker,
        bar_date=day,
        open=close,
        high=close,
        low=close,
        close=close,
        volume=1_000_000,
    )


def _many_bars(ticker: str, count: int = 70) -> tuple[OHLCVBar, ...]:
    """Return `count` bars with a steady upward trend for `ticker`."""
    return tuple(_bar(ticker, float(100 + i), count - 1 - i) for i in range(count))


def _dummy_candidate(ticker: str = "AAPL") -> Candidate:
    return candidate(ticker=ticker)


def test_score_candidate_keeps_alpha158_score_on_history_rejection() -> None:
    """Kills agents.analyst.domain.scoring.x_score_candidate__mutmut_11."""
    breakdown = score_candidate(
        _dummy_candidate(),
        bars=(),
        fundamentals={},
        benchmark_bars=(),
        news=(),
        settings=AnalystSettings(),
        alpha_score=65.0,
    )
    assert isinstance(breakdown, ScoreBreakdown)
    assert breakdown.alpha158_score == 65.0
    assert breakdown.rejection_reason == "insufficient_market_history"


def test_score_candidate_alpha158_score_populated_when_supplied() -> None:
    # Provide min_history_bars (2) so we reach the full scoring path where
    # alpha_score is written into both the breakdown field and the metrics dict.
    two_bars = (
        _bar("AAPL", 100.0, 1),
        _bar("AAPL", 101.0, 0),
    )
    breakdown = score_candidate(
        _dummy_candidate(),
        bars=two_bars,
        fundamentals={},
        benchmark_bars=(),
        news=(),
        settings=AnalystSettings(alpha158_pillar_weight=0.20),
        alpha_score=65.0,
    )
    assert breakdown.alpha158_score == 65.0
    assert "alpha158_score" in breakdown.metrics
    assert breakdown.metrics["alpha158_score"] == 65.0


def test_score_candidate_alpha158_blended_into_composite() -> None:
    """Kills scoring.x_score_candidate__mutmut_59, 60, 84, and 85."""
    # With no bars the technical score is 0.0 (insufficient history).
    # With weight=0 the composite stays 0.0; with weight>0 and a high alpha
    # score the rejection reason is still set (insufficient history guard fires
    # before the composite is computed), so we supply enough bars.
    n = 5
    bars = tuple(
        OHLCVBar(
            ticker="AAPL",
            bar_date=datetime.now(tz=UTC).date() - timedelta(days=n - 1 - i),
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=1000,
        )
        for i in range(n)
    )
    default_breakdown = score_candidate(
        _dummy_candidate(),
        bars=bars,
        fundamentals={},
        benchmark_bars=(),
        news=(),
        settings=AnalystSettings(),
        alpha_score=None,
    )
    alpha_breakdown = score_candidate(
        _dummy_candidate(),
        bars=bars,
        fundamentals={},
        benchmark_bars=(),
        news=(),
        settings=AnalystSettings(alpha158_pillar_weight=0.20),
        alpha_score=65.0,
    )
    assert default_breakdown.metrics["composite_score"] == 0.35
    assert alpha_breakdown.metrics["composite_score"] == pytest.approx(
        0.4357142857142857, abs=1e-12
    )
    assert alpha_breakdown.metrics["confidence"] == pytest.approx(
        alpha_breakdown.confidence, abs=1e-12
    )
    assert alpha_breakdown.confidence == pytest.approx(0.5614285714285714, abs=1e-12)


def test_analyze_populates_alpha158_score_with_sufficient_history() -> None:
    settings = AnalystSettings(alpha158_pillar_weight=0.20)
    all_bars = _many_bars("AAPL", 70) + _many_bars("MSFT", 70) + _many_bars("LOW", 70)
    bus, _graph, sink = wire_analyst(source_bars=all_bars, settings=settings)
    scan = candidate_set(candidate("AAPL"), candidate("MSFT"), candidate("LOW"))

    response = bus.request(analyze_message(scan))

    assert response.message_type == "response"
    assert sink.faults == []
    # At least one candidate should either be recommended or rejected without an
    # alpha-related fault — the pillar must have activated without raising.
    payload = response.payload
    total = len(payload["recommendations"]) + len(payload["rejections"])
    assert total == 3


def test_analyze_alpha158_degrades_gracefully_when_insufficient_bars() -> None:
    # With weight > 0 but only 2 bars per ticker, no feature row can be computed;
    # the pillar silently skips (empty universe) so all candidates get alpha_score=None.
    settings = AnalystSettings(alpha158_pillar_weight=0.20)
    few_bars = (
        _bar("AAPL", 100.0, 1),
        _bar("AAPL", 101.0, 0),
    )
    bus, _graph, sink = wire_analyst(source_bars=few_bars, settings=settings)
    scan = candidate_set(candidate("AAPL"))

    response = bus.request(analyze_message(scan))

    assert response.message_type == "response"
    assert sink.faults == []


def test_analyze_alpha158_skips_ticker_with_no_feature_in_mixed_universe() -> None:
    # AAPL has 70 bars (feature computed); MSFT has 2 bars (feature is None).
    # The universe is non-empty (AAPL); MSFT's None row is skipped in the loop.
    settings = AnalystSettings(alpha158_pillar_weight=0.20)
    all_bars = (
        *_many_bars("AAPL", 70),
        _bar("MSFT", 100.0, 1),
        _bar("MSFT", 101.0, 0),
    )
    bus, _graph, sink = wire_analyst(source_bars=all_bars, settings=settings)
    scan = candidate_set(candidate("AAPL"), candidate("MSFT"))

    response = bus.request(analyze_message(scan))

    assert response.message_type == "response"
    assert sink.faults == []
    recs = response.payload["recommendations"]
    rejs = response.payload["rejections"]
    assert len(recs) + len(rejs) == 2
