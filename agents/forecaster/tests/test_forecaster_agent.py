"""Forecaster agent end-to-end tests.

Agent: forecaster
Role: verify forecast persistence/response, neutral fallbacks (no news, provider
      fault, model fault), and the never-promoting scorecard.
External I/O: none.
"""

from __future__ import annotations

from agents.forecaster.model import FakeSentimentModel
from agents.forecaster.tests.helpers import (
    forecast_message,
    scorecard_message,
    wire_forecaster,
)
from contracts.forecaster import Scorecard, ShadowPrediction


def _key_of(graph_node_id: str) -> str:
    return graph_node_id.split(":", 1)[1]


def test_forecast_persists_and_returns_a_shadow_prediction() -> None:
    """FORE-IN-01 / FORE-TRG-01 / FORE-OUT-01 / FORE-OUT-05: RPC →
    ShadowPrediction with node written."""
    model = FakeSentimentModel(per_headline={"Beats": 0.9, "Grows": 0.7})
    bus, graph, sink = wire_forecaster(news={"AAPL": ("Beats", "Grows")}, model=model)

    response = bus.request(forecast_message("AAPL"))

    prediction = ShadowPrediction.model_validate(response.payload)
    assert prediction.shadow is True
    assert prediction.value == 0.8
    assert prediction.confidence == 0.4
    assert prediction.subject_ref == "AAPL"
    assert sink.faults == []
    assert prediction.provenance.graph_node_id is not None
    node = graph.get_node(
        "ShadowPrediction", _key_of(prediction.provenance.graph_node_id)
    )
    assert node is not None


def test_forecast_with_no_news_is_neutral_zero_confidence() -> None:
    """FORE-OUT-06: no news → neutral value=0.5, confidence=0.0; shadow=True."""
    bus, _graph, sink = wire_forecaster(news={})

    prediction = ShadowPrediction.model_validate(
        bus.request(forecast_message("AAPL")).payload
    )
    assert prediction.value == 0.5
    assert prediction.confidence == 0.0
    assert prediction.shadow is True
    assert sink.faults == []


def test_forecast_survives_a_provider_fault() -> None:
    """FORE-FAIL-02 / FORE-NEV-04: provider fault → neutral shadow."""
    bus, _graph, _sink = wire_forecaster(news={"AAPL": ("x",)}, fail_news=True)

    prediction = ShadowPrediction.model_validate(
        bus.request(forecast_message("AAPL")).payload
    )
    assert prediction.value == 0.5
    assert prediction.confidence == 0.0
    assert prediction.shadow is True


def test_forecast_handles_a_provider_error_response() -> None:
    # No provider registered -> the bus answers with an error message; the news
    # request degrades to empty and the forecast still yields a neutral shadow.
    bus, _graph, _sink = wire_forecaster(register_provider=False)

    prediction = ShadowPrediction.model_validate(
        bus.request(forecast_message("AAPL")).payload
    )
    assert prediction.value == 0.5
    assert prediction.confidence == 0.0
    assert prediction.shadow is True


class _RaisingModel:
    def score_headlines(self, headlines: tuple[str, ...]) -> tuple[float, ...]:
        del headlines
        raise RuntimeError("model down")


def test_forecast_falls_back_to_neutral_on_a_model_fault() -> None:
    """FORE-FAIL-01: model exception → neutral prediction; fault captured."""
    bus, _graph, sink = wire_forecaster(news={"AAPL": ("x",)}, model=_RaisingModel())

    prediction = ShadowPrediction.model_validate(
        bus.request(forecast_message("AAPL")).payload
    )
    assert prediction.value == 0.5
    assert prediction.confidence == 0.0
    assert sink.faults  # the model fault was captured, not raised to the caller


def test_scorecard_reports_samples_and_never_promotes() -> None:
    """FORE-IN-03 / FORE-OUT-03 / FORE-OUT-04: scorecard; promotion_eligible=False."""
    model = FakeSentimentModel(default=0.6)
    bus, _graph, _sink = wire_forecaster(
        news={"AAPL": ("a",), "MSFT": ("b",)}, model=model
    )
    bus.request(forecast_message("AAPL"))
    bus.request(forecast_message("MSFT"))

    card = Scorecard.model_validate(
        bus.request(scorecard_message("finbert-sentiment")).payload
    )
    assert card.sample_size == 2
    assert card.promotion_eligible is False
    assert card.metrics["mean_value"] == 0.6


def test_scorecard_for_an_unknown_model_is_empty() -> None:
    bus, _graph, _sink = wire_forecaster(news={})

    card = Scorecard.model_validate(bus.request(scorecard_message("unknown")).payload)
    assert card.sample_size == 0
    assert card.metrics["mean_confidence"] == 0.0
    assert card.promotion_eligible is False
