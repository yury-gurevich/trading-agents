"""Geometric-pattern edge assertions for mutation hardening.

Agent: analyst
Role: pin exact threshold and last-swing behaviour in pattern helpers.
External I/O: none.
"""

from __future__ import annotations

from agents.analyst.domain import indicators_pattern as ip


def _flat(
    n: int = 20, value: float = 100.0
) -> tuple[list[float], list[float], list[float]]:
    return [value] * n, [value] * n, [value] * n


def _set(
    series: tuple[list[float], list[float], list[float]], index: int, value: float
) -> None:
    series[0][index] = series[1][index] = series[2][index] = value


def test_geometric_patterns_allows_exact_twenty_bar_pattern_window() -> None:
    """Kills indicators_pattern.x_geometric_patterns__mutmut_6."""
    series = _flat(20)
    for index, value in ((4, 120.0), (12, 120.0), (8, 90.0)):
        _set(series, index, value)

    assert ip.geometric_patterns(series[0], series[1], series[2], 20, 2.0) == (
        "double_top",
        0.85,
    )


def test_geometric_patterns_converts_swing_percent_to_exact_tolerance() -> None:
    """Kills indicators_pattern.x_geometric_patterns__mutmut_23."""
    series = _flat(24)
    for index, value in ((4, 120.0), (12, 122.388), (8, 90.0)):
        _set(series, index, value)
    _set(series, 23, 117.0)

    assert ip.geometric_patterns(series[0], series[1], series[2], 24, 2.0) == (
        "double_top",
        0.0,
    )


def test_find_swing_filter_uses_last_close_not_previous() -> None:
    """Kills indicators_pattern.x_find_swing_points__mutmut_31."""
    closes = [100.0] * 7
    highs = [100.0] * 7
    lows = [100.0] * 7
    highs[3] = 101.5
    closes[-2] = 101.0

    assert ip.find_swing_points(closes, highs, lows, 2.0) == [(3, 101.5, "high")]


def test_find_swing_filter_keeps_empty_swings_with_zero_last_close() -> None:
    """Kills indicators_pattern.x_find_swing_points__mutmut_32."""
    closes = [100.0, 100.0, 100.0, 100.0, 0.0]
    highs = [100.0] * 5
    lows = [100.0] * 5

    assert ip.find_swing_points(closes, highs, lows, 2.0) == []


def test_find_swing_filter_zero_last_close_returns_unfiltered_swings() -> None:
    """Kills indicators_pattern.x_find_swing_points__mutmut_35."""
    closes = [100.0] * 7
    highs = [100.0] * 7
    lows = [100.0] * 7
    highs[3] = 110.0
    closes[-1] = 0.0

    assert ip.find_swing_points(closes, highs, lows, 2.0) == [(3, 110.0, "high")]


def test_matching_swings_is_open_at_exact_tolerance() -> None:
    """Kills indicators_pattern.x__matching_swings__mutmut_4."""
    assert ip._matching_swings(100.0, 102.0, 0.02) is False


def test_double_top_rejects_short_gap_and_boundary_break() -> None:
    """Kills _double_pattern mutmut_9, mutmut_10, and mutmut_19."""
    assert ip._double_pattern([(3, 120.0), (4, 120.0)], [], 100.0, 0.02) is None
    assert ip._double_pattern([(4, 120.0), (9, 120.0)], [], 117.0, 0.02) == (
        "double_top",
        0.85,
    )
    assert ip._double_pattern([(4, 120.0), (12, 120.0)], [], 117.6, 0.02) is None


def test_double_bottom_rejects_short_gap_and_boundary_break() -> None:
    """Kills _double_pattern mutmut_49, mutmut_50, and mutmut_59."""
    assert ip._double_pattern([], [(3, 80.0), (4, 80.0)], 100.0, 0.02) is None
    assert ip._double_pattern([], [(4, 80.0), (9, 80.0)], 82.0, 0.02) == (
        "double_bottom",
        0.85,
    )
    assert ip._double_pattern([], [(4, 80.0), (12, 80.0)], 81.6, 0.02) is None


def test_head_and_shoulders_requires_all_head_shoulders_and_break_terms() -> None:
    """Kills _shoulder_pattern mutmut_21 through mutmut_25."""
    assert (
        ip._shoulder_pattern([(1, 100.0), (7, 120.0), (13, 80.0)], [], 200.0, 0.02)
        is None
    )
    assert (
        ip._shoulder_pattern([(1, 100.0), (7, 120.0), (13, 150.0)], [], 200.0, 0.02)
        is None
    )
    assert (
        ip._shoulder_pattern([(1, 120.0), (7, 120.0), (13, 119.0)], [], 100.0, 0.02)
        is None
    )
    assert (
        ip._shoulder_pattern([(1, 119.0), (7, 120.0), (13, 120.0)], [], 100.0, 0.02)
        is None
    )
    assert (
        ip._shoulder_pattern([(1, 120.0), (7, 130.0), (13, 120.0)], [], 120.0, 0.02)
        is None
    )


def test_inverse_head_and_shoulders_requires_all_head_shoulders_and_break_terms() -> (
    None
):
    """Kills _shoulder_pattern mutmut_52 through mutmut_56."""
    assert (
        ip._shoulder_pattern([], [(1, 100.0), (7, 80.0), (13, 120.0)], 50.0, 0.02)
        is None
    )
    assert (
        ip._shoulder_pattern([], [(1, 100.0), (7, 80.0), (13, 50.0)], 50.0, 0.02)
        is None
    )
    assert (
        ip._shoulder_pattern([], [(1, 80.0), (7, 80.0), (13, 81.0)], 100.0, 0.02)
        is None
    )
    assert (
        ip._shoulder_pattern([], [(1, 81.0), (7, 80.0), (13, 80.0)], 100.0, 0.02)
        is None
    )
    assert (
        ip._shoulder_pattern([], [(1, 80.0), (7, 70.0), (13, 80.0)], 80.0, 0.02) is None
    )
