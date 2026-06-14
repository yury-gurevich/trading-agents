"""Golden-value tests for pure-Python range-based indicators.

Agent: analyst
Role: pin hand-computed ATR/Stochastic/Williams/Choppiness values and None paths.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.analyst.domain import indicators_range as ir


def test_true_ranges_match_hand_values() -> None:
    highs = [11.0, 12.0, 13.0, 12.5, 14.0]
    lows = [9.0, 10.0, 11.0, 10.5, 12.0]
    closes = [10.0, 11.0, 12.0, 11.5, 13.0]
    # TR_1=2, TR_2=2, TR_3=2, TR_4=max(2, 2.5, 0.5)=2.5
    assert ir._true_ranges(highs, lows, closes) == [2.0, 2.0, 2.0, 2.5]


def test_atr_is_mean_of_last_period_true_ranges() -> None:
    highs = [11.0, 12.0, 13.0, 12.5, 14.0]
    lows = [9.0, 10.0, 11.0, 10.5, 12.0]
    closes = [10.0, 11.0, 12.0, 11.5, 13.0]
    # mean of last 2 TRs (2.0, 2.5) = 2.25
    assert ir.atr(highs, lows, closes, 2) == pytest.approx(2.25, abs=1e-9)


def test_atr_returns_none_below_period_plus_one() -> None:
    assert ir.atr([1.0, 2.0], [1.0, 2.0], [1.0, 2.0], 2) is None


def test_stochastic_close_at_window_high_is_one_hundred() -> None:
    result = ir.stochastic([10.0, 10.0, 12.0], [8.0, 8.0, 8.0], [9.0, 9.0, 12.0], 3, 1)
    assert result == (100.0, 100.0)


def test_stochastic_close_at_window_low_is_zero() -> None:
    result = ir.stochastic([10.0, 10.0, 12.0], [8.0, 8.0, 8.0], [9.0, 9.0, 8.0], 3, 1)
    assert result == (0.0, 0.0)


def test_stochastic_flat_window_is_fifty() -> None:
    result = ir.stochastic([5.0, 5.0, 5.0], [5.0, 5.0, 5.0], [5.0, 5.0, 5.0], 3, 1)
    assert result == (50.0, 50.0)


def test_stochastic_returns_none_below_k_plus_d_minus_one() -> None:
    assert ir.stochastic([5.0, 5.0], [5.0, 5.0], [5.0, 5.0], 3, 1) is None


def test_williams_close_at_high_is_zero() -> None:
    value = ir.williams_r([10.0, 10.0, 12.0], [8.0, 8.0, 8.0], [9.0, 9.0, 12.0], 3)
    assert value == pytest.approx(0.0)


def test_williams_close_at_low_is_minus_one_hundred() -> None:
    value = ir.williams_r([10.0, 10.0, 12.0], [8.0, 8.0, 8.0], [9.0, 9.0, 8.0], 3)
    assert value == -100.0


def test_williams_flat_window_is_minus_fifty() -> None:
    assert ir.williams_r([5.0, 5.0, 5.0], [5.0, 5.0, 5.0], [5.0, 5.0, 5.0], 3) == -50.0


def test_williams_returns_none_below_period() -> None:
    assert ir.williams_r([5.0, 5.0], [5.0, 5.0], [5.0, 5.0], 3) is None


def test_choppiness_trending_series_is_low() -> None:
    rising = [100.0, 101.0, 102.0, 103.0, 104.0]
    # sum last-4 TR = 4; rng over last-4 H/L = 104-101 = 3; CI = 100*log10(4/3)/log10(4)
    value = ir.choppiness(rising, rising, rising, 4)
    assert value == pytest.approx(20.75187496394219, abs=1e-9)


def test_choppiness_oscillating_series_is_high() -> None:
    highs = [110.0] * 5
    lows = [100.0] * 5
    closes = [100.0, 110.0, 100.0, 110.0, 100.0]
    # sum last-4 TR = 40; rng = 10; CI = 100*log10(40/10)/log10(4) = 100.0
    value = ir.choppiness(highs, lows, closes, 4)
    assert value == pytest.approx(100.0, abs=1e-9)


def test_choppiness_flat_range_returns_none() -> None:
    assert ir.choppiness([5.0] * 5, [5.0] * 5, [5.0] * 5, 4) is None


def test_choppiness_returns_none_below_period_plus_one() -> None:
    assert ir.choppiness([5.0] * 4, [5.0] * 4, [5.0] * 4, 4) is None
