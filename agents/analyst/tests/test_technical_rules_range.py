"""Boundary tests for range-indicator scoring rules.

Agent: analyst
Role: pin the exact 0-100 band boundaries for ATR/Stochastic/Williams/Choppiness.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.analyst.domain import indicators_range
from agents.analyst.domain import technical_rules_range as rules
from agents.analyst.settings import AnalystSettings


@pytest.mark.parametrize(
    ("atr_pct", "expected"),
    [(1.99, 70.0), (2.0, 55.0), (3.99, 55.0), (4.0, 35.0)],
)
def test_score_atr_bands(atr_pct: float, expected: float) -> None:
    assert rules.score_atr(atr_pct) == expected


@pytest.mark.parametrize(
    ("percent_k", "percent_d", "expected"),
    [
        (19.0, 19.0, 80.0),
        (19.0, 20.0, 65.0),
        (20.0, 19.0, 50.0),
        (19.0, 50.0, 65.0),
        (85.0, 85.0, 20.0),
        (81.0, 80.0, 35.0),
        (80.0, 81.0, 50.0),
        (85.0, 50.0, 35.0),
        (50.0, 50.0, 50.0),
        (20.0, 20.0, 50.0),
        (80.0, 80.0, 50.0),
    ],
)
def test_score_stochastic_bands(
    percent_k: float, percent_d: float, expected: float
) -> None:
    """Kills x_score_stochastic__mutmut_2, 3, 8, and 9."""
    assert rules.score_stochastic(percent_k, percent_d) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(-81.0, 75.0), (-80.0, 50.0), (-20.0, 50.0), (-19.0, 25.0)],
)
def test_score_williams_bands(value: float, expected: float) -> None:
    assert rules.score_williams(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(38.1, 75.0), (38.2, 50.0), (61.8, 50.0), (61.9, 30.0)],
)
def test_score_choppiness_bands(value: float, expected: float) -> None:
    assert rules.score_choppiness(value) == expected


def test_range_indicator_scores_pins_stochastic_and_metric_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kills technical_rules_range.x_range_indicator_scores mutmut_37, 42, 55,
    56, 69, and 70.
    """
    monkeypatch.setattr(indicators_range, "atr", lambda *_args: None)
    monkeypatch.setattr(indicators_range, "stochastic", lambda *_args: (10.0, 50.0))
    monkeypatch.setattr(indicators_range, "williams_r", lambda *_args: -90.0)
    monkeypatch.setattr(indicators_range, "choppiness", lambda *_args: 70.0)

    assert rules.range_indicator_scores([1.0], [1.0], [1.0], AnalystSettings()) == [
        ("stochastic_k", 10.0, 65.0),
        ("williams_r", -90.0, 75.0),
        ("choppiness", 70.0, 30.0),
    ]
