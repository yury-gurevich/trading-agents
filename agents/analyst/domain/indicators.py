"""Pure-Python technical indicator calculations.

Agent: analyst
Role: compute RSI/MACD/Bollinger/SMA/EMA from close-price history; no I/O, no pandas.
External I/O: none.
"""

from __future__ import annotations

from itertools import pairwise
from math import sqrt

_RSI_MAX = 100.0


def _mean(values: list[float]) -> float:
    """Arithmetic mean of a non-empty list (caller guarantees length)."""
    return sum(values) / len(values)


def _sma(values: list[float], period: int) -> float:
    """Simple mean of the last ``period`` values (caller guarantees length)."""
    return _mean(values[-period:])


def _pstdev(values: list[float]) -> float:
    """Population standard deviation (0.0 for a single value)."""
    if len(values) < 2:
        return 0.0
    mu = _mean(values)
    variance = sum((value - mu) ** 2 for value in values) / len(values)
    return sqrt(variance)


def _ema(values: list[float], period: int) -> float:
    """Exponential moving average seeded with the simple mean of the first window."""
    return _ema_series(values, period)[-1]


def _ema_series(values: list[float], period: int) -> list[float]:
    """Per-step EMA over ``values``, seeded with the SMA of the first ``period``."""
    multiplier = 2.0 / (period + 1)
    ema = _mean(values[:period])
    series = [ema]
    for value in values[period:]:
        ema = (value - ema) * multiplier + ema
        series.append(ema)
    return series


def rsi(closes: list[float], period: int) -> float | None:
    """RSI over the last ``period`` deltas; ``None`` below ``period + 1`` closes."""
    if len(closes) < period + 1:
        return None
    window = closes[-(period + 1) :]
    gains = [max(b - a, 0.0) for a, b in pairwise(window)]
    losses = [max(a - b, 0.0) for a, b in pairwise(window)]
    avg_loss = _mean(losses)
    if avg_loss == 0.0:
        return _RSI_MAX
    rs = _mean(gains) / avg_loss
    return _RSI_MAX - _RSI_MAX / (1 + rs)


def macd(
    closes: list[float], fast: int, slow: int, signal: int
) -> tuple[float, float, float] | None:
    """MACD ``(line, signal, histogram)``; ``None`` below ``slow + signal`` closes."""
    if len(closes) < slow + signal:
        return None
    fast_series = _ema_series(closes, fast)
    slow_series = _ema_series(closes, slow)
    aligned = fast_series[-len(slow_series) :]
    macd_series = [f - s for f, s in zip(aligned, slow_series, strict=True)]
    line = macd_series[-1]
    signal_line = _ema(macd_series, signal)
    return line, signal_line, line - signal_line


def bollinger_position(closes: list[float], window: int, sigma: float) -> float | None:
    """Position of the last close within its bands [0,1]; ``None`` below ``window``."""
    if len(closes) < window:
        return None
    mid = _sma(closes, window)
    spread = sigma * _pstdev(closes[-window:])
    upper, lower = mid + spread, mid - spread
    if upper == lower:
        return 0.5
    position = (closes[-1] - lower) / (upper - lower)
    return max(0.0, min(1.0, position))


def sma_distance(closes: list[float], period: int) -> float | None:
    """Percent distance of the last close from its SMA; ``None`` below ``period``."""
    if len(closes) < period:
        return None
    sma = _sma(closes, period)
    return (closes[-1] - sma) / sma * 100.0


def ema_crossover_spread(closes: list[float], short: int, long: int) -> float | None:
    """Percent spread of the short EMA over the long EMA; ``None`` below ``long``."""
    if len(closes) < long:
        return None
    short_ema = _ema(closes, short)
    long_ema = _ema(closes, long)
    return (short_ema - long_ema) / long_ema * 100.0
