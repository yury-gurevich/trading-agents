"""Decision-time favorable-excursion metric collection.

Agent: analyst
Role: derive target-upside metrics from already-fetched OHLCV bars.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.analyst.domain.stop_target_outcome import (
    FAVORABLE_EXCURSION_HORIZON_DAYS,
    FAVORABLE_EXCURSION_LOOKBACK_WINDOWS,
    FAVORABLE_EXCURSION_PCT,
    FAVORABLE_EXCURSION_SAMPLE_COUNT,
    trailing_favorable_excursion,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from agents.analyst.settings import AnalystSettings
    from contracts.provider import OHLCVBar


def target_excursion_metrics(
    rows: Sequence[OHLCVBar], settings: AnalystSettings
) -> dict[str, float]:
    """Return favorable-excursion metrics for the latest decision bar."""
    horizon = settings.stop_target_drawdown_horizon_days
    lookback = settings.stop_target_excursion_lookback_windows
    estimate = trailing_favorable_excursion(rows, rows[-1].bar_date, horizon, lookback)
    metrics = {
        FAVORABLE_EXCURSION_HORIZON_DAYS: float(horizon),
        FAVORABLE_EXCURSION_LOOKBACK_WINDOWS: float(lookback),
        FAVORABLE_EXCURSION_SAMPLE_COUNT: 0.0,
    }
    if estimate is not None:
        metrics[FAVORABLE_EXCURSION_PCT] = estimate.excursion_pct
        metrics[FAVORABLE_EXCURSION_SAMPLE_COUNT] = float(estimate.sample_count)
    return metrics
