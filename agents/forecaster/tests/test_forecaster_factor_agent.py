"""Forecaster factor-shadow agent tests.

Agent: forecaster
Role: verify forecast_factor default-off behavior, advisory writes, and scorecards.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from agents.forecaster.domain.features import squash
from agents.forecaster.settings import ForecasterSettings
from agents.forecaster.tests.helpers import (
    make_bars,
    scorecard_message,
    wire_forecaster,
)
from agents.forecaster.tests.return_helpers import forecast_factor_message
from contracts.forecaster import Scorecard, ShadowPrediction

if TYPE_CHECKING:
    from contracts.provider import OHLCVBar


def test_forecast_factor_disabled_by_default_refuses_without_graph_write() -> None:
    bus, graph, sink = wire_forecaster(bars=_bars())

    prediction = ShadowPrediction.model_validate(
        bus.request(forecast_factor_message("AAPL")).payload
    )

    assert prediction.model_id == "factor-disabled"
    assert prediction.value == 0.5
    assert prediction.confidence == 0.0
    assert prediction.shadow is True
    assert prediction.provenance.graph_node_id is None
    assert graph.list_nodes("ShadowPrediction") == ()
    assert graph.list_nodes("Model") == ()
    assert sink.faults == []


def test_forecast_factor_enabled_writes_shadow_only_prediction() -> None:
    """FORE-NEV-02 / FORE-OUT-02: factor forecasts advise; they never gate or size."""
    settings = ForecasterSettings(
        factor_name="momentum",
        factor_params="lookback=5",
        bars_for_full_confidence=10,
    )
    bus, graph, sink = wire_forecaster(bars=_bars(), settings=settings)

    prediction = ShadowPrediction.model_validate(
        bus.request(forecast_factor_message("AAPL")).payload
    )

    assert prediction.model_id == "factor-momentum-5"
    assert prediction.value == pytest.approx(squash(5.0 / 105.0, scale=0.05))
    assert prediction.confidence == 1.0
    assert prediction.shadow is True
    assert sink.faults == []
    assert len(graph.list_nodes("ShadowPrediction")) == 1
    model = graph.get_node("Model", "factor-momentum-5")
    assert model is not None
    assert model.props["kind"] == "factor"
    assert graph.list_nodes("OrderIntent") == ()
    assert graph.list_nodes("PMRun") == ()
    assert graph.list_nodes("CloseDecision") == ()


def test_forecast_factor_invalid_operator_params_refuse_without_write() -> None:
    settings = ForecasterSettings(
        factor_name="momentum",
        factor_params="lookback=4",
        factor_model_id="factor-approved-momentum",
    )
    bus, graph, _sink = wire_forecaster(bars=_bars(), settings=settings)

    prediction = ShadowPrediction.model_validate(
        bus.request(forecast_factor_message("AAPL")).payload
    )

    assert prediction.model_id == "factor-approved-momentum"
    assert prediction.value == 0.5
    assert prediction.confidence == 0.0
    assert graph.list_nodes("ShadowPrediction") == ()


def test_forecast_factor_too_few_bars_writes_neutral_shadow() -> None:
    settings = ForecasterSettings(factor_name="momentum", factor_params="lookback=5")
    bus, graph, _sink = wire_forecaster(
        bars=make_bars("AAPL", (100.0, 101.0, 102.0)), settings=settings
    )

    prediction = ShadowPrediction.model_validate(
        bus.request(forecast_factor_message("AAPL")).payload
    )

    assert prediction.model_id == "factor-momentum-5"
    assert prediction.value == 0.5
    assert prediction.confidence == 0.0
    assert len(graph.list_nodes("ShadowPrediction")) == 1


def test_generic_scorecard_covers_factor_predictions_and_never_promotes() -> None:
    settings = ForecasterSettings(
        factor_name="momentum",
        factor_params="lookback=5",
        factor_model_id="factor-approved-momentum",
    )
    bus, _graph, _sink = wire_forecaster(bars=_bars(), settings=settings)
    bus.request(forecast_factor_message("AAPL"))
    bus.request(forecast_factor_message("AAPL"))

    card = Scorecard.model_validate(
        bus.request(scorecard_message("factor-approved-momentum")).payload
    )

    assert card.sample_size == 2
    assert card.metrics["mean_confidence"] > 0.0
    assert card.promotion_eligible is False


def _bars() -> tuple[OHLCVBar, ...]:
    return make_bars("AAPL", tuple(100.0 + index for index in range(11)))
