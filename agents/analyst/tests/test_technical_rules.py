"""Boundary tests for indicator scoring rules and the composite.

Agent: analyst
Role: pin the 0-100 band boundaries and the available-only averaging.
External I/O: none.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from agents.analyst.domain import indicators
from agents.analyst.domain import technical_rules as rules
from agents.analyst.settings import AnalystSettings
from contracts.provider import OHLCVBar


def _ramp_bars(length: int) -> list[OHLCVBar]:
    """A rising trend that dips every 5th bar with cycling volume and +/-2 H/L spread.

    The periodic dips give OBV genuine up *and* down steps (not a trivial monotone
    series), and the 1.00M/1.25M/1.50M volume cycle makes each OBV step distinct, so
    the volume/event group is exercised meaningfully rather than degenerately.
    """
    base = date(2025, 1, 1)
    rows = []
    for i in range(length):
        close = 100.0 + i - (2.0 if (i % 5 == 0 and i > 0) else 0.0)
        rows.append(
            OHLCVBar(
                ticker="AAPL",
                bar_date=base + timedelta(days=i),
                open=close,
                high=close + 2.0,
                low=close - 2.0,
                close=close,
                volume=1_000_000 + (i % 3) * 250_000,
            )
        )
    return rows


@pytest.mark.parametrize(
    ("value", "expected"),
    [(29.999, 80.0), (30.0, 65.0), (49.999, 65.0), (50.0, 50.0), (70.0, 25.0)],
)
def test_score_rsi_bands(value: float, expected: float) -> None:
    assert rules.score_rsi(value) == expected


@pytest.mark.parametrize(
    ("line", "histogram", "expected"),
    [
        (1.0, 1.0, 75.0),
        (0.0, 1.0, 60.0),
        (-1.0, 1.0, 60.0),
        (-1.0, -1.0, 25.0),
        (-1.0, 0.0, 45.0),
        (0.0, -1.0, 45.0),
        (1.0, 0.0, 45.0),
    ],
)
def test_score_macd_bands(line: float, histogram: float, expected: float) -> None:
    """Kills x_score_macd__mutmut_2, 10, 11, 12, 13, and 14."""
    assert rules.score_macd(line, histogram) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0.299, 75.0), (0.30, 50.0), (0.699, 50.0), (0.70, 30.0)],
)
def test_score_bollinger_bands(value: float, expected: float) -> None:
    assert rules.score_bollinger(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(5.001, 75.0), (5.0, 60.0), (0.0, 40.0), (-5.0, 20.0)],
)
def test_score_sma_distance_bands(value: float, expected: float) -> None:
    assert rules.score_sma_distance(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(1.001, 75.0), (1.0, 60.0), (0.0, 40.0), (-1.0, 25.0)],
)
def test_score_ema_crossover_bands(value: float, expected: float) -> None:
    assert rules.score_ema_crossover(value) == expected


def test_score_technical_all_fourteen_available_matches_mean() -> None:
    """Kills x_score_technical__mutmut_10, x__momentum_scores__mutmut_27."""
    raw, metrics = rules.score_technical(_ramp_bars(220), AnalystSettings())
    # 220 dipping-ramp bars -> 5 momentum + 4 range + 3 event + 2 pattern available
    # (the smooth ramp forms no geometric pattern, so only NW + turnaround of the
    # pattern group emit): RSI 25, MACD 75, Bollinger 30, SMA 75, EMA 75 | ATR 70,
    # Stochastic 20, Williams 25, Choppiness 50 | OBV 70, golden cross 75, RSI-2 20 |
    # NW +2.05% -> 30, turnaround (last bar Fri, not Mon) -> 50. Prior 610 + 80 = 690.
    assert metrics["indicators_available"] == 14.0
    assert metrics["sma_distance_pct"] == pytest.approx(45.59561843906892, abs=1e-12)
    assert metrics["ema_spread_pct"] == pytest.approx(5.114878485505306, abs=1e-12)
    assert metrics["atr_pct"] == pytest.approx(1.3210927004030453, abs=1e-12)
    assert metrics["obv"] == 165750000.0
    assert raw == pytest.approx(690.0 / 14.0, abs=1e-9)


def test_score_technical_partial_history_averages_available_only() -> None:
    """Kills x_score_technical__mutmut_17 and x__momentum_scores__mutmut_52."""
    raw, metrics = rules.score_technical(_ramp_bars(40), AnalystSettings())
    # 40 bars -> RSI 25, MACD 75, Bollinger 30 | ATR 55, Stochastic 20, Williams 25,
    # Choppiness 50 | OBV 70 (needs 21), RSI-2 20 (needs 3) | NW +4.82% -> 30 (needs
    # 10), turnaround (last bar Sun) -> 50 (needs 3); SMA-200, EMA-50, golden cross
    # (needs 200) and any geometric pattern unavailable -> prior 370 + 80 = 450 / 11.
    assert metrics["indicators_available"] == 11.0
    assert metrics["macd_histogram"] == pytest.approx(0.059810341477100515, abs=1e-12)
    assert metrics["bollinger_position"] == pytest.approx(0.9154532910262163, abs=1e-12)
    assert metrics["nw_deviation_pct"] == pytest.approx(4.8228510175484125, abs=1e-12)
    assert raw == pytest.approx(450.0 / 11.0, abs=1e-9)


def test_momentum_scores_use_macd_line_for_macd_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kills agents.analyst.domain.technical_rules._momentum_scores__mutmut_49."""
    monkeypatch.setattr(indicators, "rsi", lambda *_args: None)
    monkeypatch.setattr(indicators, "bollinger_position", lambda *_args: None)
    monkeypatch.setattr(indicators, "sma_distance", lambda *_args: None)
    monkeypatch.setattr(indicators, "ema_crossover_spread", lambda *_args: None)
    monkeypatch.setattr(indicators, "macd", lambda *_args: (-1.0, 1.0, -1.0))

    assert rules._momentum_scores([1.0] * 40, AnalystSettings()) == [
        ("macd_histogram", -1.0, 25.0)
    ]


def test_score_technical_neutral_when_no_indicator_available() -> None:
    # Two bars is below every window (RSI-2 alone needs three closes), so the
    # composite fully degrades to the neutral 50 with no indicators available.
    assert rules.score_technical(_ramp_bars(2), AnalystSettings()) == (
        50.0,
        {"indicators_available": 0.0},
    )
