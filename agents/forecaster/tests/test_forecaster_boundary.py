"""Forecaster boundary tests — the never-clauses.

Agent: forecaster
Role: prove every forecast is shadow, the scorecard never self-promotes, and the
      contract declares no external I/O.
External I/O: none.
"""

from __future__ import annotations

from agents.forecaster.tests.helpers import (
    forecast_message,
    scorecard_message,
    wire_forecaster,
)
from contracts.forecaster import CONTRACT, Scorecard, ShadowPrediction


def test_every_forecast_is_a_shadow_signal() -> None:
    bus, _graph, _sink = wire_forecaster(news={"AAPL": ("rallies",)})
    prediction = ShadowPrediction.model_validate(
        bus.request(forecast_message("AAPL")).payload
    )
    assert prediction.shadow is True


def test_scorecard_is_never_promotion_eligible() -> None:
    model_id = "finbert-sentiment"
    bus, _graph, _sink = wire_forecaster(news={"AAPL": ("rallies",)})
    bus.request(forecast_message("AAPL"))
    card = Scorecard.model_validate(bus.request(scorecard_message(model_id)).payload)
    assert card.promotion_eligible is False


def test_contract_declares_never_clauses_and_no_external_io() -> None:
    assert len(CONTRACT.never) == 3
    assert CONTRACT.external_io == ()
    assert CONTRACT.owns_graph == ("ShadowPrediction", "Model")
