"""Return-model port tests.

Agent: forecaster
Role: verify the deterministic fake returns a fixed score or a function output.
External I/O: none.
"""

from __future__ import annotations

from agents.forecaster.domain.features import FeatureRow
from agents.forecaster.return_model import FakeReturnModel

_ROW = FeatureRow(0.1, 0.2, 0.3, 0.4, 0.5, 0.6)


def test_fake_return_model_returns_the_fixed_raw_score() -> None:
    assert FakeReturnModel(0.3).predict(_ROW) == 0.3


def test_fake_return_model_defaults_to_zero() -> None:
    assert FakeReturnModel().predict(_ROW) == 0.0


def test_fake_return_model_applies_a_feature_function() -> None:
    model = FakeReturnModel(fn=lambda row: row.ret_mid)
    assert model.predict(_ROW) == 0.2
