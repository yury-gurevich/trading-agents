"""Boundary tests for volume/event scoring rules and their composite group.

Agent: analyst
Role: pin the exact 0-100 band boundaries for OBV / golden cross / RSI-2.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.analyst.domain import indicators, indicators_event
from agents.analyst.domain import technical_rules_event as rules
from agents.analyst.settings import AnalystSettings


@pytest.mark.parametrize(
    ("obv_value", "signal", "expected"),
    [(101.0, 100.0, 70.0), (99.0, 100.0, 35.0), (100.0, 100.0, 35.0)],
)
def test_score_obv_bands(obv_value: float, signal: float, expected: float) -> None:
    # Strict ``>``: OBV equal to its signal is distribution (35), not accumulation.
    assert rules.score_obv(obv_value, signal) == expected


@pytest.mark.parametrize(("is_golden", "expected"), [(True, 75.0), (False, 25.0)])
def test_score_golden_cross_bands(is_golden: bool, expected: float) -> None:
    assert rules.score_golden_cross(is_golden) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(9.9, 80.0), (10.0, 50.0), (90.0, 50.0), (90.1, 20.0)],
)
def test_score_rsi2_bands(value: float, expected: float) -> None:
    # Strict ``<`` / ``>``: exactly 10 or 90 falls into the neutral band.
    assert rules.score_rsi2(value) == expected


def test_event_indicator_scores_returns_all_three_when_available() -> None:
    closes = [100.0 + i for i in range(200)]  # rising: golden, OBV up, RSI-2 hot
    volumes = [1_000_000.0] * 200
    triples = rules.event_indicator_scores(closes, volumes, AnalystSettings())
    assert [name for name, _value, _score in triples] == ["obv", "golden_cross", "rsi2"]
    assert [score for _name, _value, score in triples] == [70.0, 75.0, 20.0]
    # The golden-cross boolean is stored as a 1.0/0.0 float metric value.
    assert triples[1][1] == 1.0


def test_event_indicator_scores_false_golden_cross_value_is_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kills technical_rules_event.x_event_indicator_scores__mutmut_30."""
    monkeypatch.setattr(indicators_event, "obv", lambda *_args: None)
    monkeypatch.setattr(indicators_event, "golden_cross", lambda *_args: False)
    monkeypatch.setattr(indicators, "rsi", lambda *_args: None)

    assert rules.event_indicator_scores(
        [1.0] * 200, [1.0] * 200, AnalystSettings()
    ) == [("golden_cross", 0.0, 25.0)]


def test_event_indicator_scores_skips_unavailable_indicators() -> None:
    # 21 bars: OBV (needs 21) and RSI-2 (needs 3) fire; golden cross (needs 200) skips.
    closes = [100.0 + i for i in range(21)]
    volumes = [1_000_000.0] * 21
    triples = rules.event_indicator_scores(closes, volumes, AnalystSettings())
    assert [name for name, _value, _score in triples] == ["obv", "rsi2"]


def test_event_indicator_scores_empty_when_nothing_available() -> None:
    closes, volumes = [100.0, 101.0], [1e6, 1e6]
    triples = rules.event_indicator_scores(closes, volumes, AnalystSettings())
    assert triples == []
