"""Feature/label pair construction for offline LightGBM training.

Agent: forecaster
Role: build no-lookahead (feature_row, forward_return) pairs from a ticker's
      date-sorted OHLCV bars; the offline training script passes these to the
      model trainer.
External I/O: none (pure functions over in-memory bar sequences).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.forecaster.domain.features import build_features

if TYPE_CHECKING:
    from agents.forecaster.domain.features import FeatureRow


@dataclass(frozen=True)
class LabelRow:
    """Training example: features at as_of_date + realized forward return."""

    ticker: str
    as_of_date: str  # ISO "YYYY-MM-DD"; walk-forward split sorts on this
    features: FeatureRow
    forward_return: float  # closes[i+forward_days]/closes[i] - 1.0


def build_label_rows(
    ticker_bars: dict[str, list[tuple[str, float, float]]],
    *,
    forward_days: int,
    horizons: tuple[int, int, int],
    volatility_window: int,
    momentum_window: int,
) -> list[LabelRow]:
    """Build training pairs for every ticker; empty list when no ticker qualifies.

    ``ticker_bars`` maps each ticker to a date-ascending list of
    ``(date_iso, close, volume)`` tuples.  For each index ``i`` where:
    - ``build_features`` returns a non-None row (enough history), and
    - ``i + forward_days`` is within the bar series (forward return is known),

    one ``LabelRow`` is appended.  Features use only bars up to index ``i``
    (no lookahead); the forward return uses the bar at ``i + forward_days``.
    """
    rows: list[LabelRow] = []
    for ticker, bars in ticker_bars.items():
        closes = tuple(close for _, close, _ in bars)
        volumes = tuple(vol for _, _, vol in bars)
        dates = [date for date, _, _ in bars]
        for i in range(len(bars) - forward_days):
            features = build_features(
                closes[: i + 1],
                volumes[: i + 1],
                horizons=horizons,
                volatility_window=volatility_window,
                momentum_window=momentum_window,
            )
            if features is None:
                continue
            forward_return = closes[i + forward_days] / closes[i] - 1.0
            rows.append(LabelRow(ticker, dates[i], features, forward_return))
    return rows
