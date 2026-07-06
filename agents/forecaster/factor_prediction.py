"""Forecast-factor graph write/refusal wrapper.

Agent: forecaster
Role: keep optional factor shadow predictions advisory-only and operator-gated.
External I/O: none (provider bars are requested through the injected bus).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.forecaster.domain.sentiment import NEUTRAL
from agents.forecaster.factor_signal import read_factor
from agents.forecaster.store import write_forecast
from contracts.common import Provenance
from contracts.forecaster import ForecastRequest, ShadowPrediction

if TYPE_CHECKING:
    from pydantic import BaseModel

    from agents.forecaster.settings import ForecasterSettings
    from kernel import FaultSink, GraphStore, MessageBus


def forecast_factor(
    graph: GraphStore,
    bus: MessageBus,
    sink: FaultSink,
    settings: ForecasterSettings,
    request: BaseModel,
) -> ShadowPrediction:
    """Return an advisory factor shadow prediction when explicitly enabled."""
    forecast = ForecastRequest.model_validate(request)
    factor = read_factor(bus, sink, settings, forecast.subject_ref)
    if factor is None:
        return _disabled_factor_prediction(forecast, settings.factor_model_id)
    provenance = write_forecast(
        graph,
        model_id=factor.model_id,
        model_ref=factor.model_ref,
        subject_kind=forecast.subject_kind,
        subject_ref=forecast.subject_ref,
        reading=factor.reading,
        model_kind="factor",
    )
    return ShadowPrediction(
        model_id=factor.model_id,
        subject_ref=forecast.subject_ref,
        value=factor.reading.value,
        confidence=factor.reading.confidence,
        provenance=provenance,
    )


def _disabled_factor_prediction(
    forecast: ForecastRequest, factor_model_id: str
) -> ShadowPrediction:
    model_id = factor_model_id
    if not model_id:
        model_id = "factor-disabled"
    return ShadowPrediction(
        model_id=model_id,
        subject_ref=forecast.subject_ref,
        value=NEUTRAL,
        confidence=0.0,
        provenance=Provenance(run_id="factor-disabled", source_agent="forecaster"),
    )
