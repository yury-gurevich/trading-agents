"""Price/return feature engineering for the LightGBM shadow signal.

Agent: forecaster
Role: turn a subject's trailing close/volume series into a small, no-lookahead
      feature row, and squash a raw model output onto the shared 0-1 scale.
External I/O: none (pure functions over in-memory price series).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureRow:
    """A small, fixed-order feature vector built from trailing daily bars."""

    ret_short: float
    ret_mid: float
    ret_long: float
    volatility: float
    momentum: float
    volume_ratio: float

    def as_vector(self) -> tuple[float, ...]:
        """Return the features in a fixed canonical order (the model input order)."""
        return (
            self.ret_short,
            self.ret_mid,
            self.ret_long,
            self.volatility,
            self.momentum,
            self.volume_ratio,
        )


def build_features(
    closes: tuple[float, ...],
    volumes: tuple[float, ...],
    *,
    horizons: tuple[int, int, int],
    volatility_window: int,
    momentum_window: int,
) -> FeatureRow | None:
    """Build a no-lookahead feature row from trailing bars; None if too short.

    ``closes`` and ``volumes`` are the subject's bars in ascending date order and
    of equal length (the same bar series). Every feature looks only backward from
    the most recent bar, so there is no lookahead.
    """
    short, mid, long = horizons
    needed = max(long, volatility_window, momentum_window) + 1
    if len(closes) < needed:
        return None
    return FeatureRow(
        ret_short=_trailing_return(closes, short),
        ret_mid=_trailing_return(closes, mid),
        ret_long=_trailing_return(closes, long),
        volatility=_volatility(closes, volatility_window),
        momentum=_momentum(closes, momentum_window),
        volume_ratio=_volume_ratio(volumes, momentum_window),
    )


def squash(raw: float, *, scale: float) -> float:
    """Map a raw predicted return onto 0-1 via a logistic; 0.5 at raw 0."""
    return 1.0 / (1.0 + math.exp(-raw / scale))


def confidence_from_history(bars: int, *, full_confidence_bars: int) -> float:
    """Confidence as the trailing-history fill ratio, capped at 1.0."""
    return min(bars / full_confidence_bars, 1.0)


def _trailing_return(closes: tuple[float, ...], horizon: int) -> float:
    return closes[-1] / closes[-1 - horizon] - 1.0


def _volatility(closes: tuple[float, ...], window: int) -> float:
    return _stdev(_daily_returns(closes[-window - 1 :]))


def _momentum(closes: tuple[float, ...], window: int) -> float:
    return closes[-1] / (sum(closes[-window:]) / window) - 1.0


def _volume_ratio(volumes: tuple[float, ...], window: int) -> float:
    mean = sum(volumes[-window:]) / window
    return volumes[-1] / mean - 1.0 if mean > 0.0 else 0.0


def _daily_returns(closes: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes)))


def _stdev(values: tuple[float, ...]) -> float:
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(variance)
