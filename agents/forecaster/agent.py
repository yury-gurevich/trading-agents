"""Forecaster agent implementation.

Agent: forecaster
Role: produce advisory shadow predictions and barrier claims, and report model
      scorecards; every output is shadow and never gates a decision.
External I/O: none (the model and provider sit behind injected ports / the bus).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from functools import partial
from typing import TYPE_CHECKING

from agents.forecaster.barrier_fit import ArchGarchFitter
from agents.forecaster.barrier_forecast import forecast_barrier
from agents.forecaster.domain.sentiment import NEUTRAL, ModelReading, aggregate
from agents.forecaster.factor_prediction import forecast_factor
from agents.forecaster.model import FakeSentimentModel
from agents.forecaster.price_signal import read_return
from agents.forecaster.provider_client import request_news
from agents.forecaster.return_model import FakeReturnModel
from agents.forecaster.scorecards import (
    return_scorecard,
    scorecard,
    sentiment_scorecard,
)
from agents.forecaster.settings import ForecasterSettings
from agents.forecaster.store import write_forecast
from contracts.common import Window
from contracts.forecaster import CONTRACT, ForecastRequest, ShadowPrediction
from kernel import AgentBase, CollectingFaultSink, FaultSink, GraphStore
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from pydantic import BaseModel

    from agents.forecaster.barrier_fit import GarchFitter
    from agents.forecaster.model import SentimentModel
    from agents.forecaster.return_model import ReturnModel
    from kernel import MessageBus


class ForecasterAgent(AgentBase):
    """Advisory shadow-ML forecaster (sentiment); never gates a decision."""

    def __init__(
        self,
        bus: MessageBus,
        *,
        graph: GraphStore,
        model: SentimentModel | None = None,
        return_model: ReturnModel | None = None,
        settings: ForecasterSettings | None = None,
        sink: FaultSink | None = None,
        barrier_fitter: GarchFitter | None = None,
    ) -> None:
        """Create the forecaster with injected bus, graph, models, settings, sink.

        The barrier fitter defaults to the real arch adapter, never a fake: a
        missing ``arch`` is a fault and no claim (FORE-FAIL-04).
        """
        super().__init__(CONTRACT, bus)
        self._graph = graph
        self._model = model if model is not None else FakeSentimentModel()
        self._return_model = (
            return_model if return_model is not None else FakeReturnModel()
        )
        self._settings = settings or ForecasterSettings()
        self.sink = sink if sink is not None else CollectingFaultSink()
        self._barrier_fitter = (
            barrier_fitter if barrier_fitter is not None else ArchGarchFitter()
        )
        self.handlers = {
            "forecast": self._forecast,
            "forecast_return": self._forecast_return,
            "forecast_factor": self._forecast_factor,
            "forecast_barrier": self._forecast_barrier,
            "scorecard": partial(scorecard, graph),
            "sentiment_scorecard": partial(sentiment_scorecard, graph),
            "return_scorecard": partial(return_scorecard, graph),
        }

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

    def _forecast_return(self, request: BaseModel) -> ShadowPrediction:
        forecast = ForecastRequest.model_validate(request)
        reading = read_return(
            self.bus,
            self.sink,
            self._return_model,
            self._settings,
            forecast.subject_ref,
        )
        provenance = write_forecast(
            self._graph,
            model_id=self._settings.return_model_id,
            model_ref=self._settings.return_model_ref,
            subject_kind=forecast.subject_kind,
            subject_ref=forecast.subject_ref,
            reading=reading,
            model_kind="return",
        )
        return ShadowPrediction(
            model_id=self._settings.return_model_id,
            subject_ref=forecast.subject_ref,
            value=reading.value,
            confidence=reading.confidence,
            provenance=provenance,
        )

    def _forecast_factor(self, request: BaseModel) -> ShadowPrediction:
        return forecast_factor(
            self._graph, self.bus, self.sink, self._settings, request
        )

    def _forecast_barrier(self, request: BaseModel) -> ShadowPrediction:
        return forecast_barrier(
            self._graph,
            self.sink,
            self._settings,
            self._barrier_fitter,
            request,
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
