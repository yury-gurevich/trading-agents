"""Golden-value tests for pure-Python volume/event indicators.

Agent: analyst
Role: pin hand-computed OBV and golden-cross values and their None paths.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.analyst.domain import indicators_event as ie


def test_obv_accumulates_by_close_direction_with_carry() -> None:
    """Kills x_obv__mutmut_19, x_obv__mutmut_20, and x_obv__mutmut_24."""
    closes = [10.0, 11.0, 11.0, 10.0, 12.0]
    volumes = [100.0, 200.0, 300.0, 400.0, 500.0]
    # series: 0 -> +200 (up) -> 200 (carry, unchanged close) -> -400 (down) ->
    # +500 (up) = [0, 200, 200, -200, 300]; signal = mean(last 3) = (200-200+300)/3.
    assert ie.obv(closes, volumes, 3) == pytest.approx((300.0, 100.0), abs=1e-9)


def test_obv_signal_uses_requested_tail_window() -> None:
    """Kills agents.analyst.domain.indicators_event.x_obv__mutmut_26."""
    closes = [10.0, 12.0, 11.0, 13.0, 13.0, 12.0, 14.0]
    volumes = [100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0]
    assert ie.obv(closes, volumes, 4) == pytest.approx((400.0, 175.0), abs=1e-9)


def test_obv_returns_none_below_signal_period_plus_one() -> None:
    closes = [10.0, 11.0, 11.0]
    volumes = [100.0, 200.0, 300.0]
    assert ie.obv(closes, volumes, 3) is None


def test_golden_cross_short_above_long_is_true() -> None:
    assert ie.golden_cross([1.0, 2.0, 3.0, 4.0, 5.0], 2, 4) is True


def test_golden_cross_short_below_long_is_false() -> None:
    assert ie.golden_cross([5.0, 4.0, 3.0, 2.0, 1.0], 2, 4) is False


def test_golden_cross_equal_smas_is_false() -> None:
    # Equal averages are not a strict cross (``>``), so a flat series is not golden.
    assert ie.golden_cross([5.0, 5.0, 5.0, 5.0], 2, 4) is False


def test_golden_cross_returns_none_below_long() -> None:
    assert ie.golden_cross([1.0, 2.0, 3.0], 2, 4) is None
