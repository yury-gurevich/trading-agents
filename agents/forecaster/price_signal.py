"""Price/return shadow scoring: bars -> features -> model -> advisory reading.

Agent: forecaster
Role: turn a subject ticker into an advisory price/return ModelReading using the
      provider's OHLCV and the injected ReturnModel; degrades to neutral on no
      data or a model fault (never raises to the caller).
External I/O: none (provider answers over the bus; the model sits behind a port).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from agents.forecaster.domain.features import (
    build_features,
    confidence_from_history,
    squash,
)
from agents.forecaster.domain.sentiment import NEUTRAL, ModelReading
from agents.forecaster.provider_client import request_prices
from contracts.common import Window
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from agents.forecaster.domain.features import FeatureRow
    from agents.forecaster.return_model import ReturnModel
    from agents.forecaster.settings import ForecasterSettings
    from kernel import FaultSink, MessageBus


def read_return(
    bus: MessageBus,
    sink: FaultSink,
    model: ReturnModel,
    settings: ForecasterSettings,
    ticker: str,
) -> ModelReading:
    """Fetch bars, build features, score; neutral on no data or a model fault."""
    bars = request_prices(bus, sink, ticker, _window(settings))
    features = build_features(
        tuple(bar.close for bar in bars),
        tuple(float(bar.volume) for bar in bars),
        horizons=(
            settings.return_short_horizon,
            settings.return_mid_horizon,
            settings.return_long_horizon,
        ),
        volatility_window=settings.volatility_window,
        momentum_window=settings.momentum_window,
    )
    if features is None:
        return ModelReading(NEUTRAL, 0.0)
    raw = _predict(model, sink, features)
    if raw is None:
        return ModelReading(NEUTRAL, 0.0)
    return ModelReading(
        squash(raw, scale=settings.return_squash_scale),
        confidence_from_history(
            len(bars), full_confidence_bars=settings.bars_for_full_confidence
        ),
    )


def _predict(model: ReturnModel, sink: FaultSink, features: FeatureRow) -> float | None:
    raw: float | None = None
    with fault_boundary(
        sink,
        agent="forecaster",
        module="agents.forecaster.price_signal",
        capability="forecast_return",
        reraise=False,
    ) as capture:
        raw = model.predict(features)
    return None if capture.fault is not None else raw


def _window(settings: ForecasterSettings) -> Window:
    end = datetime.now(tz=UTC).date()
    start = end - timedelta(days=settings.price_lookback_days)
    return Window(start=start, end=end)
