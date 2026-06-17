"""Forecaster sentiment-domain tests.

Agent: forecaster
Role: verify the pure label-alignment and aggregation reducers.
External I/O: none.
"""

from __future__ import annotations

from agents.forecaster.domain.sentiment import (
    NEUTRAL,
    ModelReading,
    aggregate,
    align_label,
)


def test_align_label_positive_pushes_above_neutral() -> None:
    assert align_label("positive", 0.8) == NEUTRAL + NEUTRAL * 0.8


def test_align_label_negative_pushes_below_neutral() -> None:
    assert align_label("NEGATIVE", 0.6) == NEUTRAL - NEUTRAL * 0.6


def test_align_label_neutral_or_unknown_stays_neutral() -> None:
    assert align_label("neutral", 0.9) == NEUTRAL
    assert align_label("garbled", 1.0) == NEUTRAL


def test_aggregate_means_scores_and_scales_confidence() -> None:
    reading = aggregate((1.0, 0.0, 0.5), headlines_for_full_confidence=5)
    assert reading == ModelReading(value=0.5, confidence=0.6)


def test_aggregate_saturates_confidence_at_full_count() -> None:
    reading = aggregate((0.2, 0.4, 0.6, 0.8, 1.0, 0.5), headlines_for_full_confidence=5)
    assert reading is not None
    assert reading.confidence == 1.0


def test_aggregate_returns_none_when_there_is_nothing_to_score() -> None:
    assert aggregate((), headlines_for_full_confidence=5) is None
