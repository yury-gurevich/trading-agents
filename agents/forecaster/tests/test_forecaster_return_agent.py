"""Forecaster return-model agent tests.

Agent: forecaster
Role: verify forecast_return persistence/response and neutral fallbacks (too few bars,
      provider fault, model fault, no provider).
External I/O: none.
"""

from __future__ import annotations

from agents.forecaster.domain.features import squash
from agents.forecaster.return_model import FakeReturnModel
from agents.forecaster.tests.helpers import make_bars, wire_forecaster
from agents.forecaster.tests.return_helpers import forecast_return_message
from contracts.forecaster import ShadowPrediction


def _key_of(graph_node_id: str) -> str:
    return graph_node_id.split(":", 1)[1]


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
    bus, _graph, sink = wire_forecaster(
        bars=bars, return_model=FakeReturnModel(raw=0.9)
    )

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
