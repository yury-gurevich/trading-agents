"""Forecaster store tests.

Agent: forecaster
Role: verify Model + ShadowPrediction persistence, the PREDICTED edge, the guarded
      ADVISES edge, and model-scoped prediction reads.
External I/O: none.
"""

from __future__ import annotations

from agents.forecaster.domain.sentiment import ModelReading
from agents.forecaster.store import _advise_subject, read_predictions, write_forecast
from kernel import InMemoryGraphStore


def _key_of(graph_node_id: str) -> str:
    return graph_node_id.split(":", 1)[1]


def test_write_forecast_persists_model_and_shadow_prediction() -> None:
    graph = InMemoryGraphStore()
    provenance = write_forecast(
        graph,
        model_id="finbert-sentiment",
        model_ref="ProsusAI/finbert",
        subject_kind="recommendation",
        subject_ref="AAPL",
        reading=ModelReading(value=0.8, confidence=0.4),
    )
    model = graph.get_node("Model", "finbert-sentiment")
    assert model is not None
    assert model.props["kind"] == "sentiment"
    assert provenance.graph_node_id is not None
    prediction = graph.get_node("ShadowPrediction", _key_of(provenance.graph_node_id))
    assert prediction is not None
    assert prediction.props["value"] == 0.8
    assert prediction.props["shadow"] is True
    assert prediction.props["model_id"] == "finbert-sentiment"
    children = [node.label for node in graph.descendants(model, max_depth=1)]
    assert children == ["ShadowPrediction"]


def test_write_forecast_links_advises_when_subject_present() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node("Recommendation", "AAPL", {"ticker": "AAPL"})
    write_forecast(
        graph,
        model_id="m",
        model_ref="r",
        subject_kind="recommendation",
        subject_ref="AAPL",
        reading=ModelReading(value=0.6, confidence=0.5),
    )
    recommendation = graph.get_node("Recommendation", "AAPL")
    assert recommendation is not None
    parents = [node.label for node in graph.ancestors(recommendation, max_depth=1)]
    assert parents == ["ShadowPrediction"]


def test_advise_subject_ignores_an_unknown_subject_kind() -> None:
    graph = InMemoryGraphStore()
    prediction = graph.merge_node("ShadowPrediction", "p", {})
    _advise_subject(graph, prediction, "macro", "X")
    assert list(graph.descendants(prediction, max_depth=1)) == []


def test_advise_subject_skips_an_absent_subject_node() -> None:
    graph = InMemoryGraphStore()
    prediction = graph.merge_node("ShadowPrediction", "p", {})
    _advise_subject(graph, prediction, "position", "MISSING")
    assert list(graph.descendants(prediction, max_depth=1)) == []


def test_read_predictions_filters_by_model_id() -> None:
    graph = InMemoryGraphStore()
    for model_id, ticker in (("a", "AAPL"), ("b", "MSFT")):
        write_forecast(
            graph,
            model_id=model_id,
            model_ref="r",
            subject_kind="recommendation",
            subject_ref=ticker,
            reading=ModelReading(value=0.5, confidence=0.1),
        )
    predictions = read_predictions(graph, "a")
    assert len(predictions) == 1
    assert predictions[0].props["model_id"] == "a"


def test_write_forecast_records_a_custom_model_kind() -> None:
    graph = InMemoryGraphStore()
    write_forecast(
        graph,
        model_id="lgbm-return-v1",
        model_ref="lightgbm-gbdt",
        subject_kind="recommendation",
        subject_ref="AAPL",
        reading=ModelReading(value=0.7, confidence=0.5),
        model_kind="return",
    )
    model = graph.get_node("Model", "lgbm-return-v1")
    assert model is not None
    assert model.props["kind"] == "return"
