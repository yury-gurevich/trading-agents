"""Deterministic multi-year daily-bar series for the S239 barrier tests.

Agent: forecaster
Role: generate a stock's highs, lows and closes from closed-form arithmetic only
      (no RNG, no numpy), so the same series exists in the unit gate and in the
      scratch environment that ran EXP-018's own function to pin A2's golden values.
External I/O: none.
"""

from __future__ import annotations

import math

#: Opening level of every synthetic series.
START = 100.0


def ohlc_series(
    count: int, *, drift: float = 0.0, swing: float = 0.012
) -> tuple[list[float], list[float], list[float], list[float]]:
    """Return ``(opens, highs, lows, closes)`` for ``count`` daily bars.

    Each day opens at the prior close and moves by ``drift`` plus a bounded,
    volatility-clustered swing; the high and low sit outside the open and close.
    """
    opens: list[float] = []
    highs: list[float] = []
    lows: list[float] = []
    closes: list[float] = []
    close = START
    for index in range(count):
        wave = math.sin(index * 1.37) * (1.0 + 0.5 * math.cos(index * 0.071))
        open_ = close
        close = open_ * math.exp(drift + swing * wave)
        opens.append(open_)
        highs.append(max(open_, close) * (1.004 + 0.003 * abs(math.sin(index * 0.53))))
        lows.append(min(open_, close) * (0.996 - 0.003 * abs(math.cos(index * 0.29))))
        closes.append(close)
    return opens, highs, lows, closes
