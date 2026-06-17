"""Forecaster fake-model tests.

Agent: forecaster
Role: verify the deterministic per-headline fake scorer.
External I/O: none.
"""

from __future__ import annotations

from agents.forecaster.domain.sentiment import NEUTRAL
from agents.forecaster.model import FakeSentimentModel


def test_fake_model_uses_default_for_unknown_headlines() -> None:
    model = FakeSentimentModel(default=0.7)
    assert model.score_headlines(("a", "b")) == (0.7, 0.7)


def test_fake_model_uses_per_headline_overrides() -> None:
    model = FakeSentimentModel(per_headline={"good news": 0.9}, default=0.2)
    assert model.score_headlines(("good news", "other")) == (0.9, 0.2)


def test_fake_model_defaults_to_neutral() -> None:
    assert FakeSentimentModel().score_headlines(("x",)) == (NEUTRAL,)
