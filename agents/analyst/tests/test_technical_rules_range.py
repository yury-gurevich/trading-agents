"""Boundary tests for range-indicator scoring rules.

Agent: analyst
Role: pin the exact 0-100 band boundaries for ATR/Stochastic/Williams/Choppiness.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.analyst.domain import technical_rules_range as rules


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
        (19.0, 50.0, 65.0),
        (85.0, 85.0, 20.0),
        (85.0, 50.0, 35.0),
        (50.0, 50.0, 50.0),
        (20.0, 20.0, 50.0),
        (80.0, 80.0, 50.0),
    ],
)
def test_score_stochastic_bands(
    percent_k: float, percent_d: float, expected: float
) -> None:
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
