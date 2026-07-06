"""Runtime reader for advisory factor shadow signals.

Agent: forecaster
Role: fetch provider bars through the bus and convert enabled factors to readings.
External I/O: none (provider owns market-data I/O behind the bus).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from agents.forecaster.domain.factor_signal import (
    FactorSelection,
    latest_score,
    model_id,
    model_ref,
    parse_selection,
)
from agents.forecaster.domain.features import confidence_from_history, squash
from agents.forecaster.domain.sentiment import NEUTRAL, ModelReading
from agents.forecaster.provider_client import request_prices
from contracts.common import Window

if TYPE_CHECKING:
    from agents.forecaster.settings import ForecasterSettings
    from contracts.provider import OHLCVBar
    from kernel import FaultSink, MessageBus


@dataclass(frozen=True)
class FactorReading:
    """Enabled factor model identity plus its current advisory reading."""

    model_id: str
    model_ref: str
    reading: ModelReading


def configured_selection(settings: ForecasterSettings) -> FactorSelection | None:
    """Return the operator-enabled factor, or None when off/invalid."""
    return parse_selection(settings.factor_name, settings.factor_params)


def read_factor(
    bus: MessageBus,
    sink: FaultSink,
    settings: ForecasterSettings,
    ticker: str,
) -> FactorReading | None:
    """Read one enabled factor through the existing provider bars seam."""
    selection = configured_selection(settings)
    if selection is None:
        return None
    bars = request_prices(
        bus, sink, ticker, _window(settings), capability="forecast_factor"
    )
    raw = latest_score(selection, _bars(ticker, bars))
    reading = (
        ModelReading(NEUTRAL, 0.0)
        if raw is None
        else ModelReading(
            squash(raw, scale=settings.return_squash_scale),
            confidence_from_history(
                len(bars), full_confidence_bars=settings.bars_for_full_confidence
            ),
        )
    )
    return FactorReading(
        model_id=settings.factor_model_id or model_id(selection),
        model_ref=model_ref(selection),
        reading=reading,
    )


def _window(settings: ForecasterSettings) -> Window:
    end = datetime.now(tz=UTC).date()
    start = end - timedelta(days=settings.price_lookback_days)
    return Window(start=start, end=end)


def _bars(
    ticker: str, bars: tuple[OHLCVBar, ...]
) -> dict[str, list[tuple[str, float, float]]]:
    return {
        ticker: [
            (bar.bar_date.isoformat(), bar.close, float(bar.volume))
            for bar in sorted(bars, key=lambda item: item.bar_date)
        ]
    }
