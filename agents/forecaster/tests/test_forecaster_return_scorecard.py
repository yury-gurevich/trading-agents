"""Return scorecard agent end-to-end tests.

Agent: forecaster
Role: verify return_scorecard aligns persisted ShadowPredictions with injected
      forward returns, returns a non-promoting Scorecard, and degrades cleanly
      when there are no matching observations.
External I/O: none.
"""

from __future__ import annotations

from agents.forecaster.return_model import FakeReturnModel
from agents.forecaster.tests.helpers import (
    forecast_return_message,
    make_bars,
    return_scorecard_message,
    wire_forecaster,
)
from contracts.forecaster import Scorecard

_MODEL_ID = "lgbm-return-v1"
_BARS = make_bars("AAPL", tuple(100.0 + i for i in range(30)))


def test_return_scorecard_aligns_prediction_with_injected_return() -> None:
    bus, _graph, sink = wire_forecaster(
        bars=_BARS, return_model=FakeReturnModel(raw=0.05)
    )
    bus.request(forecast_return_message("AAPL"))

    card = Scorecard.model_validate(
        bus.request(return_scorecard_message(_MODEL_ID, {"AAPL": 0.03})).payload
    )

    assert card.model_id == _MODEL_ID
    assert card.sample_size == 1
    assert card.promotion_eligible is False
    assert card.metrics["complete_cases"] == 1.0
    assert card.metrics["hit_rate"] == 1.0  # predicted > 0.5, return > 0
    assert sink.faults == []


def test_return_scorecard_never_promotes() -> None:
    bus, _graph, _ = wire_forecaster(bars=_BARS, return_model=FakeReturnModel(raw=0.05))
    bus.request(forecast_return_message("AAPL"))
    bus.request(forecast_return_message("AAPL"))

    card = Scorecard.model_validate(
        bus.request(return_scorecard_message(_MODEL_ID, {"AAPL": 0.03})).payload
    )
    assert card.promotion_eligible is False


def test_return_scorecard_no_matching_ticker_is_empty() -> None:
    bus, _graph, _ = wire_forecaster(bars=_BARS, return_model=FakeReturnModel(raw=0.05))
    bus.request(forecast_return_message("AAPL"))

    card = Scorecard.model_validate(
        bus.request(return_scorecard_message(_MODEL_ID, {"MSFT": 0.03})).payload
    )
    assert card.sample_size == 0
    assert card.metrics == {}
    assert card.promotion_eligible is False


def test_return_scorecard_unknown_model_id_is_empty() -> None:
    bus, _graph, _ = wire_forecaster(bars=_BARS, return_model=FakeReturnModel(raw=0.05))
    bus.request(forecast_return_message("AAPL"))

    req = return_scorecard_message("nonexistent-model", {"AAPL": 0.03})
    card = Scorecard.model_validate(bus.request(req).payload)
    assert card.sample_size == 0
    assert card.metrics == {}


def test_return_scorecard_with_no_predictions_at_all() -> None:
    bus, _graph, _ = wire_forecaster(bars=_BARS, return_model=FakeReturnModel(raw=0.05))

    card = Scorecard.model_validate(
        bus.request(return_scorecard_message(_MODEL_ID, {"AAPL": 0.03})).payload
    )
    assert card.sample_size == 0
    assert card.promotion_eligible is False
