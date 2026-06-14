"""Boundary tests for indicator scoring rules and the composite.

Agent: analyst
Role: pin the 0-100 band boundaries and the available-only averaging.
External I/O: none.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from agents.analyst.domain import technical_rules as rules
from agents.analyst.settings import AnalystSettings
from contracts.provider import OHLCVBar


def _ramp_bars(length: int) -> list[OHLCVBar]:
    """Strictly rising bars with a constant +/-1 high/low spread (TR == 2)."""
    base = date(2025, 1, 1)
    rows = []
    for i in range(length):
        close = 100.0 + i
        rows.append(
            OHLCVBar(
                ticker="AAPL",
                bar_date=base + timedelta(days=i),
                open=close * 0.99,
                high=close + 1.0,
                low=close - 1.0,
                close=close,
                volume=1_000_000,
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
    [(1.0, 1.0, 75.0), (-1.0, 1.0, 60.0), (-1.0, -1.0, 25.0), (1.0, 0.0, 45.0)],
)
def test_score_macd_bands(line: float, histogram: float, expected: float) -> None:
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


def test_score_technical_all_nine_available_matches_mean() -> None:
    raw, metrics = rules.score_technical(_ramp_bars(220), AnalystSettings())
    # rising ramp, 5 momentum + 4 range -> RSI 25, MACD 45, Bollinger 30, SMA 75,
    # EMA 75 | ATR 70, Stochastic 20, Williams 25, Choppiness 75 -> sum 440 / 9.
    assert metrics["indicators_available"] == 9.0
    assert raw == pytest.approx(440.0 / 9.0, abs=1e-9)


def test_score_technical_partial_history_averages_available_only() -> None:
    raw, metrics = rules.score_technical(_ramp_bars(40), AnalystSettings())
    # 40 bars -> RSI 25, MACD 45, Bollinger 30 | ATR 70, Stochastic 20, Williams 25,
    # Choppiness 75 available; SMA-200 and EMA-50 unavailable -> sum 290 / 7.
    assert metrics["indicators_available"] == 7.0
    assert raw == pytest.approx(290.0 / 7.0, abs=1e-9)


def test_score_technical_neutral_when_no_indicator_available() -> None:
    assert rules.score_technical(_ramp_bars(3), AnalystSettings()) == (
        50.0,
        {"indicators_available": 0.0},
    )
