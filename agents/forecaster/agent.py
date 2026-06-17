"""Forecaster agent implementation.

Agent: forecaster
Role: produce advisory shadow sentiment predictions and report model scorecards;
      every output is shadow and never gates a decision.
External I/O: none (the model and provider sit behind injected ports / the bus).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from agents.forecaster.domain.sentiment import NEUTRAL, ModelReading, aggregate
from agents.forecaster.model import FakeSentimentModel
from agents.forecaster.provider_client import request_news
from agents.forecaster.settings import ForecasterSettings
from agents.forecaster.store import read_predictions, write_forecast
from contracts.common import Window
from contracts.forecaster import (
    CONTRACT,
    ForecastRequest,
    Scorecard,
    ScorecardRequest,
    ShadowPrediction,
)
from kernel import AgentBase, CollectingFaultSink, FaultSink, GraphStore
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from pydantic import BaseModel

    from agents.forecaster.model import SentimentModel
    from kernel import MessageBus, Node


class ForecasterAgent(AgentBase):
    """Advisory shadow-ML forecaster (sentiment); never gates a decision."""

    def __init__(
        self,
        bus: MessageBus,
        *,
        graph: GraphStore,
        model: SentimentModel | None = None,
        settings: ForecasterSettings | None = None,
        sink: FaultSink | None = None,
    ) -> None:
        """Create the forecaster with injected bus, graph, model, settings, sink."""
        super().__init__(CONTRACT, bus)
        self._graph = graph
        self._model = model if model is not None else FakeSentimentModel()
        self._settings = settings or ForecasterSettings()
        self.sink = sink if sink is not None else CollectingFaultSink()
        self.handlers = {"forecast": self._forecast, "scorecard": self._scorecard}

    def _forecast(self, request: BaseModel) -> ShadowPrediction:
        forecast = ForecastRequest.model_validate(request)
        reading = self._read_sentiment(forecast.subject_ref)
        provenance = write_forecast(
            self._graph,
            model_id=self._settings.model_id,
            model_ref=self._settings.model_ref,
            subject_kind=forecast.subject_kind,
            subject_ref=forecast.subject_ref,
            reading=reading,
        )
        return ShadowPrediction(
            model_id=self._settings.model_id,
            subject_ref=forecast.subject_ref,
            value=reading.value,
            confidence=reading.confidence,
            provenance=provenance,
        )

    def _scorecard(self, request: BaseModel) -> Scorecard:
        scorecard = ScorecardRequest.model_validate(request)
        predictions = read_predictions(self._graph, scorecard.model_id)
        return Scorecard(
            model_id=scorecard.model_id,
            metrics=_scorecard_metrics(predictions),
            sample_size=len(predictions),
            fresh_as_of=datetime.now(tz=UTC),
            promotion_eligible=False,
        )

    def _read_sentiment(self, ticker: str) -> ModelReading:
        news = request_news(self.bus, self.sink, ticker, self._window())
        reading = self._score(news.get(ticker, ()))
        return reading if reading is not None else ModelReading(NEUTRAL, 0.0)

    def _score(self, headlines: tuple[str, ...]) -> ModelReading | None:
        reading: ModelReading | None = None
        with fault_boundary(
            self.sink,
            agent="forecaster",
            module="agents.forecaster.agent",
            capability="forecast",
            reraise=False,
        ) as capture:
            scores = self._model.score_headlines(headlines)
            reading = aggregate(scores, self._settings.headlines_for_full_confidence)
        return None if capture.fault is not None else reading

    def _window(self) -> Window:
        end = datetime.now(tz=UTC).date()
        start = end - timedelta(days=self._settings.news_lookback_days)
        return Window(start=start, end=end)


def _scorecard_metrics(predictions: tuple[Node, ...]) -> dict[str, float]:
    if not predictions:
        return {"mean_value": NEUTRAL, "mean_confidence": 0.0}
    values = [float(node.props.get("value", NEUTRAL)) for node in predictions]
    confidences = [float(node.props.get("confidence", 0.0)) for node in predictions]
    return {
        "mean_value": sum(values) / len(values),
        "mean_confidence": sum(confidences) / len(confidences),
    }
