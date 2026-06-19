"""Alpha158 time-series feature computation.

Agent: analyst
Role: compute the 22-field Alpha158 time-series subset (ROC/STD/MAX/MIN/IMAX/IMIN at
      multiple horizons) from a sorted OHLCV bar sequence for one ticker.
External I/O: none.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.provider import OHLCVBar


@dataclass(frozen=True)
class AlphaFeatureRow:
    """Computed Alpha158 time-series subset for one ticker window."""

    # Rate-of-change at four horizons
    roc_5: float
    roc_10: float
    roc_20: float
    roc_60: float
    # Return volatility (population std of daily returns) at four horizons
    std_5: float
    std_10: float
    std_20: float
    std_60: float
    # Maximum daily return in window
    max_5: float
    max_10: float
    max_20: float
    max_60: float
    # Minimum daily return in window
    min_5: float
    min_10: float
    min_20: float
    min_60: float
    # Days-since-max position (1.0 = oldest, 0.0 = most recent), three horizons
    imax_10: float
    imax_20: float
    imax_60: float
    # Days-since-min position (1.0 = oldest, 0.0 = most recent), three horizons
    imin_10: float
    imin_20: float
    imin_60: float


def compute_alpha_features(bars: tuple[OHLCVBar, ...]) -> AlphaFeatureRow | None:
    """Compute Alpha158 time-series features from date-sorted OHLCV bars.

    Returns None when fewer than 62 bars are available (need 60-bar window + 2
    closes to derive 1 return, giving 61 daily returns with the 60-day window
    consuming the last 60 of them).
    """
    if len(bars) < 62:
        return None

    closes = [b.close for b in bars]
    n = len(closes)
    daily_returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, n)]

    def roc(w: int) -> float:
        return (closes[-1] - closes[-1 - w]) / closes[-1 - w]

    def std(w: int) -> float:
        rets = daily_returns[-w:]
        mean = sum(rets) / w
        variance = sum((r - mean) ** 2 for r in rets) / w
        return math.sqrt(variance)

    def max_ret(w: int) -> float:
        return max(daily_returns[-w:])

    def min_ret(w: int) -> float:
        return min(daily_returns[-w:])

    def imax(w: int) -> float:
        # w+1 closes → w return-periods; 0=oldest, w=most-recent
        window = closes[-w - 1 :]
        idx = window.index(max(window))
        return 1.0 - idx / w

    def imin(w: int) -> float:
        window = closes[-w - 1 :]
        idx = window.index(min(window))
        return 1.0 - idx / w

    return AlphaFeatureRow(
        roc_5=roc(5),
        roc_10=roc(10),
        roc_20=roc(20),
        roc_60=roc(60),
        std_5=std(5),
        std_10=std(10),
        std_20=std(20),
        std_60=std(60),
        max_5=max_ret(5),
        max_10=max_ret(10),
        max_20=max_ret(20),
        max_60=max_ret(60),
        min_5=min_ret(5),
        min_10=min_ret(10),
        min_20=min_ret(20),
        min_60=min_ret(60),
        imax_10=imax(10),
        imax_20=imax(20),
        imax_60=imax(60),
        imin_10=imin(10),
        imin_20=imin(20),
        imin_60=imin(60),
    )
