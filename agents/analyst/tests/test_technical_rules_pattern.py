"""Boundary tests for pattern/kernel/calendar scoring rules.

Agent: analyst
Role: pin the NW band, the directional pattern scores, and turnaround.
External I/O: none.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from agents.analyst.domain import indicators_kernel, indicators_pattern
from agents.analyst.domain import technical_rules_pattern as rules
from agents.analyst.settings import AnalystSettings


@pytest.mark.parametrize(
    ("value", "expected"),
    [(-1.1, 70.0), (-1.0, 50.0), (0.0, 50.0), (1.0, 50.0), (1.1, 30.0)],
)
def test_score_kernel_bands(value: float, expected: float) -> None:
    assert rules.score_kernel(value) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("double_bottom", 74.0),
        ("inverse_head_and_shoulders", 74.0),
        ("ascending_triangle", 74.0),
        ("double_top", 26.0),
        ("head_and_shoulders", 26.0),
        ("descending_triangle", 26.0),
    ],
)
def test_score_pattern_directional(name: str, expected: float) -> None:
    assert rules.score_pattern(name, 0.8) == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize(("is_signal", "expected"), [(True, 75.0), (False, 50.0)])
def test_score_turnaround(is_signal: bool, expected: float) -> None:
    assert rules.score_turnaround(is_signal) == expected


def _double_top() -> tuple[list[float], list[float], list[float]]:
    closes = [100.0] * 24
    highs = [100.0] * 24
    lows = [100.0] * 24
    for index, value in ((4, 120.0), (12, 120.0), (8, 90.0)):
        closes[index] = highs[index] = lows[index] = value
    closes[-1] = highs[-1] = lows[-1] = 100.0
    return closes, highs, lows


def test_pattern_indicator_scores_emits_all_three() -> None:
    closes, highs, lows = _double_top()
    dates = [date(2025, 1, 1) + timedelta(days=i) for i in range(24)]
    scored = rules.pattern_indicator_scores(
        closes, highs, lows, dates, AnalystSettings()
    )
    names = {name for name, _value, _score in scored}
    assert names == {"nw_deviation_pct", "geometric_pattern", "turnaround"}
    by_name = {name: (value, score) for name, value, score in scored}
    assert by_name["geometric_pattern"] == (0.85, 24.5)  # double_top: 50 - 0.85*30
    assert by_name["turnaround"][1] == 50.0  # last bar is a Friday, not a Monday


def test_pattern_indicator_scores_pins_pattern_and_turnaround_payloads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kills technical_rules_pattern.x_pattern_indicator_scores mutmut_30, 43,
    44, and 45.
    """
    monkeypatch.setattr(indicators_kernel, "nadaraya_watson", lambda *_args: None)
    monkeypatch.setattr(
        indicators_pattern,
        "geometric_patterns",
        lambda *_args: ("ascending_triangle", 0.80),
    )
    monkeypatch.setattr(indicators_kernel, "turnaround_signal", lambda *_args: False)

    scored = rules.pattern_indicator_scores(
        [1.0] * 20,
        [1.0] * 20,
        [1.0] * 20,
        [date(2025, 1, 1)] * 20,
        AnalystSettings(),
    )

    assert scored == [
        ("geometric_pattern", 0.80, 74.0),
        ("turnaround", 0.0, 50.0),
    ]


def test_pattern_indicator_scores_true_turnaround_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kills technical_rules_pattern.x_pattern_indicator_scores__mutmut_43
    and mutmut_45.
    """
    monkeypatch.setattr(indicators_kernel, "nadaraya_watson", lambda *_args: None)
    monkeypatch.setattr(indicators_pattern, "geometric_patterns", lambda *_args: None)
    monkeypatch.setattr(indicators_kernel, "turnaround_signal", lambda *_args: True)

    scored = rules.pattern_indicator_scores(
        [1.0] * 20,
        [1.0] * 20,
        [1.0] * 20,
        [date(2025, 1, 1)] * 20,
        AnalystSettings(),
    )

    assert scored == [("turnaround", 1.0, 75.0)]


def test_pattern_indicator_scores_skips_unavailable() -> None:
    # Two bars: NW needs 10, pattern needs 20, turnaround needs 3 -> nothing emits.
    scored = rules.pattern_indicator_scores(
        [100.0, 101.0],
        [100.0, 101.0],
        [100.0, 101.0],
        [date(2025, 1, 1), date(2025, 1, 2)],
        AnalystSettings(),
    )
    assert scored == []
