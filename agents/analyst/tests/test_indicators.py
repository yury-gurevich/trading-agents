"""Golden-value tests for pure-Python technical indicators.

Agent: analyst
Role: pin hand-computed indicator values and None on insufficient history.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.analyst.domain import indicators


def _ramp(length: int, start: float = 100.0, step: float = 1.0) -> list[float]:
    return [start + step * i for i in range(length)]


def test_rsi_rising_series_is_one_hundred() -> None:
    assert indicators.rsi(_ramp(20), 14) == 100.0


def test_rsi_mixed_series_matches_hand_value() -> None:
    deltas = [1, 2, -1, 1, -2, 3, 1, -1, 2, 1, -1, 1, 2, -1]
    closes = [100.0]
    for delta in deltas:
        closes.append(closes[-1] + delta)
    # gains sum 14 over 14 deltas -> avg_gain 1.0; losses sum 6 -> avg_loss 6/14;
    # RS = 14/6 -> RSI = 100 - 100/(1 + 14/6) = 70.0
    assert indicators.rsi(closes, 14) == pytest.approx(70.0, abs=1e-6)


def test_rsi_uses_exact_period_plus_one_window() -> None:
    """Kills agents.analyst.domain.indicators.x_rsi__mutmut_7."""
    closes = [50.0, 100.0]
    for delta in [1, 2, -1, 1, -2, 3, 1, -1, 2, 1, -1, 1, 2, -1]:
        closes.append(closes[-1] + delta)

    assert indicators.rsi(closes, 14) == pytest.approx(70.0, abs=1e-6)


def test_rsi_returns_none_below_period_plus_one() -> None:
    assert indicators.rsi(_ramp(14), 14) is None


def test_macd_rising_series_has_positive_line_and_histogram() -> None:
    """Kills x_macd__mutmut_1, x_macd__mutmut_22, and x_macd__mutmut_23."""
    closes = [
        100.0,
        101.5,
        99.0,
        104.0,
        103.0,
        108.0,
        107.0,
        112.0,
        109.0,
        115.0,
        117.0,
        116.0,
        120.0,
        119.0,
        123.0,
        125.0,
        124.0,
        128.0,
        131.0,
        130.0,
        134.0,
        136.0,
        135.0,
        139.0,
        142.0,
        140.0,
        144.0,
        146.0,
        145.0,
        149.0,
        151.0,
        150.0,
        154.0,
        156.0,
        155.0,
    ]
    assert indicators.macd(closes, 12, 26, 9) == pytest.approx(
        (11.98719989447332, 12.16914926039736, -0.18194936592403899),
        abs=1e-12,
    )


def test_macd_returns_none_below_slow_plus_signal() -> None:
    assert indicators.macd(_ramp(34), 12, 26, 9) is None


def test_bollinger_position_flat_series_is_mid_band() -> None:
    assert indicators.bollinger_position([50.0] * 25, 20, 2.0) == 0.5


def test_bollinger_position_rising_window_matches_exact_position() -> None:
    """Kills x_bollinger_position__mutmut_17 and x_bollinger_position__mutmut_18."""
    rising = [float(i) for i in range(1, 21)]
    assert indicators.bollinger_position(rising, 20, 2.0) == pytest.approx(
        0.9118772355239569
    )


def test_bollinger_position_clamps_above_upper_band() -> None:
    """Kills agents.analyst.domain.indicators.x_bollinger_position__mutmut_31."""
    closes = [10.0] * 19 + [100.0]

    assert indicators.bollinger_position(closes, 20, 0.5) == 1.0


def test_bollinger_position_returns_none_below_window() -> None:
    assert indicators.bollinger_position([1.0] * 19, 20, 2.0) is None


def test_sma_distance_above_flat_sma_is_positive_hand_value() -> None:
    series = [100.0] * 199 + [110.0]
    # sma = (199*100 + 110)/200 = 100.05; distance = (110 - 100.05)/100.05*100
    assert indicators.sma_distance(series, 200) == pytest.approx(
        9.945027486256874, abs=1e-9
    )


def test_sma_distance_returns_none_below_period() -> None:
    assert indicators.sma_distance([100.0] * 199, 200) is None


def test_ema_crossover_spread_rising_series_is_positive() -> None:
    assert indicators.ema_crossover_spread(_ramp(60), 20, 50) == pytest.approx(
        11.152416356877323, abs=1e-9
    )


def test_ema_crossover_spread_allows_exact_long_window() -> None:
    """Kills agents.analyst.domain.indicators.x_ema_crossover_spread__mutmut_1."""
    assert indicators.ema_crossover_spread(_ramp(50), 20, 50) == pytest.approx(
        12.048192771084338, abs=1e-12
    )


def test_ema_crossover_spread_returns_none_below_long() -> None:
    assert indicators.ema_crossover_spread(_ramp(49), 20, 50) is None


def test_pstdev_single_value_is_zero() -> None:
    assert indicators._pstdev([42.0]) == 0.0


def test_pstdev_two_values_uses_variance_not_singleton_guard() -> None:
    """Kills _pstdev__mutmut_1 and _pstdev__mutmut_2."""
    assert indicators._pstdev([1.0, 3.0]) == pytest.approx(1.0, abs=1e-12)


def test_pstdev_matches_hand_value() -> None:
    # population variance of [1,2,3] = ((1)+(0)+(1))/3 = 2/3; stdev = sqrt(2/3)
    assert indicators._pstdev([1.0, 2.0, 3.0]) == pytest.approx((2 / 3) ** 0.5)
