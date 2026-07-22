"""Golden-value tests for geometric chart-pattern detection.

Agent: analyst
Role: pin swing points and each hand-built (name, conf) pattern classification.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.analyst.domain import indicators_pattern as ip

_Series = tuple[list[float], list[float], list[float]]


def _flat(n: int = 24, value: float = 100.0) -> _Series:
    return [value] * n, [value] * n, [value] * n


def _set(series: _Series, index: int, value: float) -> None:
    series[0][index] = series[1][index] = series[2][index] = value


def _build(points: list[tuple[int, float]], last: float) -> _Series:
    series = _flat()
    for index, value in points:
        _set(series, index, value)
    _set(series, len(series[0]) - 1, last)
    return series


def _pattern(series: _Series) -> tuple[str, float] | None:
    return ip.geometric_patterns(series[0], series[1], series[2], 60, 2.0)


def test_find_swing_points_isolated_high_and_low() -> None:
    closes, highs, lows = _flat(11)
    closes[4] = highs[4] = 120.0
    closes[8] = lows[8] = 80.0
    assert ip.find_swing_points(closes, highs, lows, 2.0) == [
        (4, 120.0, "high"),
        (8, 80.0, "low"),
    ]


def test_find_swing_points_below_five_bars_is_empty() -> None:
    closes, highs, lows = _flat(4)
    assert ip.find_swing_points(closes, highs, lows, 2.0) == []


def test_find_swing_points_allows_exact_minimum_window() -> None:
    """Kills agents.analyst.domain.indicators_pattern.x_find_swing_points__mutmut_1."""
    closes, highs, lows = _flat(5)
    closes[2] = highs[2] = 120.0

    assert ip.find_swing_points(closes, highs, lows, 2.0) == [(2, 120.0, "high")]


def test_find_swing_points_ignores_unscannable_edges() -> None:
    """Kills agents.analyst.domain.indicators_pattern.x_find_swing_points__mutmut_5."""
    closes, highs, lows = _flat(7)
    highs[0] = closes[0] = 130.0
    lows[6] = closes[6] = 70.0

    assert ip.find_swing_points(closes, highs, lows, 2.0) == []


@pytest.mark.parametrize("blocker", [1, 2, 4, 5])
def test_find_swing_points_uses_each_high_neighbour(blocker: int) -> None:
    """Kills x_find_swing_points__mutmut_12 through x_find_swing_points__mutmut_17."""
    closes, highs, lows = _flat(7)
    closes[3] = highs[3] = 120.0
    closes[blocker] = highs[blocker] = 130.0
    expected = [(blocker, 130.0, "high")] if blocker in (2, 4) else []

    assert ip.find_swing_points(closes, highs, lows, 2.0) == expected


@pytest.mark.parametrize("blocker", [1, 2, 4, 5])
def test_find_swing_points_uses_each_low_neighbour(blocker: int) -> None:
    """Kills x_find_swing_points__mutmut_30 through x_find_swing_points__mutmut_35."""
    closes, highs, lows = _flat(7)
    closes[3] = lows[3] = 80.0
    closes[blocker] = lows[blocker] = 70.0
    expected = [(blocker, 70.0, "low")] if blocker in (2, 4) else []

    assert ip.find_swing_points(closes, highs, lows, 2.0) == expected


def test_find_swing_points_threshold_uses_final_close() -> None:
    """Kills x_find_swing_points__mutmut_30, 40, 42, 44, and 45."""
    closes, highs, lows = _flat(7, 100.0)
    highs[3] = 100.995
    closes[1] = 200.0
    closes[-1] = 100.0

    assert ip.find_swing_points(closes, highs, lows, 2.0) == []


def test_find_swing_points_keeps_exact_threshold_distance() -> None:
    """Kills agents.analyst.domain.indicators_pattern.x_find_swing_points__mutmut_45."""
    closes, highs, lows = _flat(7, 100.0)
    highs[3] = 101.0

    assert ip.find_swing_points(closes, highs, lows, 2.0) == [(3, 101.0, "high")]


def test_double_top() -> None:
    series = _build([(4, 120.0), (12, 120.0), (8, 90.0)], 100.0)
    assert _pattern(series) == ("double_top", 0.85)


def test_double_bottom() -> None:
    series = _build([(4, 80.0), (12, 80.0), (8, 110.0)], 100.0)
    assert _pattern(series) == ("double_bottom", 0.85)


def test_double_top_confidence_reflects_mismatched_swing_distance() -> None:
    """Kills agents.analyst.domain.indicators_pattern.x__double_pattern__mutmut_32."""
    pattern = ip._double_pattern([(4, 120.0), (12, 121.0)], [], 100.0, 0.02)

    assert pattern == ("double_top", 0.58)


def test_double_top_uses_the_last_two_swing_highs() -> None:
    """Kills agents.analyst.domain.indicators_pattern.x__double_pattern__mutmut_6."""
    pattern = ip._double_pattern([(2, 100.0), (8, 120.0), (16, 120.0)], [], 100.0, 0.02)

    assert pattern == ("double_top", 0.85)


def test_double_bottom_confidence_reflects_mismatched_swing_distance() -> None:
    """Kills agents.analyst.domain.indicators_pattern.x__double_pattern__mutmut_72."""
    pattern = ip._double_pattern([], [(4, 80.0), (12, 81.0)], 100.0, 0.02)

    assert pattern == ("double_bottom", 0.38)


def test_double_bottom_uses_the_last_two_swing_lows() -> None:
    """Kills agents.analyst.domain.indicators_pattern.x__double_pattern__mutmut_46."""
    pattern = ip._double_pattern([], [(2, 100.0), (8, 80.0), (16, 80.0)], 100.0, 0.02)

    assert pattern == ("double_bottom", 0.85)


def test_head_and_shoulders() -> None:
    series = _build([(4, 115.0), (10, 125.0), (16, 115.0)], 100.0)
    assert _pattern(series) == ("head_and_shoulders", 0.70)


def test_inverse_head_and_shoulders() -> None:
    series = _build([(4, 85.0), (10, 75.0), (16, 85.0)], 100.0)
    assert _pattern(series) == ("inverse_head_and_shoulders", 0.70)


def test_ascending_triangle() -> None:
    series = _build([(4, 110.0), (14, 110.0), (8, 88.0), (18, 96.0)], 108.5)
    assert _pattern(series) == ("ascending_triangle", 0.65)


def test_descending_triangle() -> None:
    series = _build([(8, 90.0), (18, 90.0), (4, 112.0), (14, 104.0)], 91.5)
    assert _pattern(series) == ("descending_triangle", 0.65)


def test_smooth_series_has_no_pattern() -> None:
    closes = [100.0 + i for i in range(24)]
    highs = [c + 0.5 for c in closes]
    lows = [c - 0.5 for c in closes]
    assert ip.geometric_patterns(closes, highs, lows, 60, 2.0) is None


def test_two_mismatched_highs_and_one_low_is_none() -> None:
    series = _build([(4, 130.0), (14, 115.0), (9, 90.0)], 100.0)
    assert _pattern(series) is None


def test_three_swings_each_side_forming_no_pattern_is_none() -> None:
    # Highs 130/118/124 and lows 80/95/70: every double, H&S and triangle test fails,
    # so the full classification chain falls through to ``None``.
    series = _flat(26)
    for index, value in (
        (3, 130.0),
        (11, 118.0),
        (19, 124.0),
        (7, 80.0),
        (15, 95.0),
        (23, 70.0),
    ):
        _set(series, index, value)
    _set(series, 25, 100.0)
    assert _pattern(series) is None


def test_below_twenty_bars_is_none() -> None:
    closes, highs, lows = _flat(15)
    assert _pattern((closes, highs, lows)) is None
