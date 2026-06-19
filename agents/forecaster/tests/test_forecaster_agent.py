"""Forecaster agent end-to-end tests.

Agent: forecaster
Role: verify forecast persistence/response, neutral fallbacks (no news, provider
      fault, model fault), and the never-promoting scorecard.
External I/O: none.
"""

from __future__ import annotations

from agents.forecaster.domain.features import squash
from agents.forecaster.model import FakeSentimentModel
from agents.forecaster.return_model import FakeReturnModel
from agents.forecaster.tests.helpers import (
    forecast_message,
    forecast_return_message,
    make_bars,
    scorecard_message,
    wire_forecaster,
)
from contracts.forecaster import Scorecard, ShadowPrediction


def _key_of(graph_node_id: str) -> str:
    return graph_node_id.split(":", 1)[1]


def test_forecast_persists_and_returns_a_shadow_prediction() -> None:
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
    bus, _graph, sink = wire_forecaster(news={})

    prediction = ShadowPrediction.model_validate(
        bus.request(forecast_message("AAPL")).payload
    )
    assert prediction.value == 0.5
    assert prediction.confidence == 0.0
    assert prediction.shadow is True
    assert sink.faults == []


def test_forecast_survives_a_provider_fault() -> None:
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
    bus, _graph, sink = wire_forecaster(news={"AAPL": ("x",)}, model=_RaisingModel())

    prediction = ShadowPrediction.model_validate(
        bus.request(forecast_message("AAPL")).payload
    )
    assert prediction.value == 0.5
    assert prediction.confidence == 0.0
    assert sink.faults  # the model fault was captured, not raised to the caller


def test_scorecard_reports_samples_and_never_promotes() -> None:
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


def test_forecast_return_persists_and_returns_a_shadow_prediction() -> None:
    bars = make_bars("AAPL", tuple(100.0 + index for index in range(30)))
    bus, graph, sink = wire_forecaster(
        bars=bars, return_model=FakeReturnModel(raw=0.05)
    )

    response = bus.request(forecast_return_message("AAPL"))

    prediction = ShadowPrediction.model_validate(response.payload)
    assert prediction.model_id == "lgbm-return-v1"
    assert prediction.value == squash(0.05, scale=0.05)
    assert prediction.confidence == 0.5
    assert prediction.shadow is True
    assert sink.faults == []
    assert prediction.provenance.graph_node_id is not None
    node = graph.get_node(
        "ShadowPrediction", _key_of(prediction.provenance.graph_node_id)
    )
    assert node is not None
    assert node.props["model_id"] == "lgbm-return-v1"


def test_forecast_return_with_too_few_bars_is_neutral() -> None:
    bars = make_bars("AAPL", (100.0, 101.0, 102.0))
    bus, _graph, sink = wire_forecaster(bars=bars, return_model=FakeReturnModel(raw=0.9))

    prediction = ShadowPrediction.model_validate(
        bus.request(forecast_return_message("AAPL")).payload
    )
    assert prediction.value == 0.5
    assert prediction.confidence == 0.0
    assert sink.faults == []


def test_forecast_return_survives_a_provider_fault() -> None:
    bars = make_bars("AAPL", tuple(100.0 + index for index in range(30)))
    bus, _graph, _sink = wire_forecaster(
        bars=bars, fail_ohlcv=True, return_model=FakeReturnModel(raw=0.9)
    )

    prediction = ShadowPrediction.model_validate(
        bus.request(forecast_return_message("AAPL")).payload
    )
    assert prediction.value == 0.5
    assert prediction.confidence == 0.0


class _RaisingReturnModel:
    def predict(self, features: object) -> float:
        del features
        raise RuntimeError("model down")


def test_forecast_return_falls_back_to_neutral_on_a_model_fault() -> None:
    bars = make_bars("AAPL", tuple(100.0 + index for index in range(30)))
    bus, _graph, sink = wire_forecaster(bars=bars, return_model=_RaisingReturnModel())

    prediction = ShadowPrediction.model_validate(
        bus.request(forecast_return_message("AAPL")).payload
    )
    assert prediction.value == 0.5
    assert prediction.confidence == 0.0
    assert sink.faults


def test_forecast_return_handles_a_provider_error_response() -> None:
    # No provider registered → bus returns an error message; request_prices degrades
    # to empty tuple and the forecast yields a neutral shadow (mirrors the news path).
    bus, _graph, _sink = wire_forecaster(register_provider=False)

    prediction = ShadowPrediction.model_validate(
        bus.request(forecast_return_message("AAPL")).payload
    )
    assert prediction.value == 0.5
    assert prediction.confidence == 0.0
    assert prediction.shadow is True
