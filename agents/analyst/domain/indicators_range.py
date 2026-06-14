"""Pure-Python range-based indicators (ATR, Stochastic, Williams %R, Choppiness).

Agent: analyst
Role: compute volatility/oscillator indicators from high/low/close history; no I/O.
External I/O: none.
"""

from __future__ import annotations

from math import log10

_STOCH_SCALE = 100.0
_WILLIAMS_SCALE = -100.0
_STOCH_FLAT = 50.0
_WILLIAMS_FLAT = -50.0


def _true_ranges(
    highs: list[float], lows: list[float], closes: list[float]
) -> list[float]:
    """True range per bar from index 1: max of H-L, |H-prev_close|, |L-prev_close|."""
    ranges: list[float] = []
    for i in range(1, len(closes)):
        prev_close = closes[i - 1]
        ranges.append(
            max(
                highs[i] - lows[i],
                abs(highs[i] - prev_close),
                abs(lows[i] - prev_close),
            )
        )
    return ranges


def atr(
    highs: list[float], lows: list[float], closes: list[float], period: int
) -> float | None:
    """Mean of the last ``period`` true ranges; ``None`` below ``period + 1`` bars."""
    if len(closes) < period + 1:
        return None
    ranges = _true_ranges(highs, lows, closes)
    window = ranges[-period:]
    return sum(window) / len(window)


def stochastic(
    highs: list[float], lows: list[float], closes: list[float], k: int, d: int
) -> tuple[float, float] | None:
    """Stochastic ``(%K, %D)``; ``None`` below ``k + d - 1`` bars."""
    if len(closes) < k + d - 1:
        return None
    k_values: list[float] = []
    for offset in range(d):
        end = len(closes) - offset
        hh = max(highs[end - k : end])
        ll = min(lows[end - k : end])
        if hh == ll:
            k_values.append(_STOCH_FLAT)
        else:
            k_values.append((closes[end - 1] - ll) / (hh - ll) * _STOCH_SCALE)
    percent_k = k_values[0]
    percent_d = sum(k_values) / len(k_values)
    return percent_k, percent_d


def williams_r(
    highs: list[float], lows: list[float], closes: list[float], period: int
) -> float | None:
    """Williams %R in [-100, 0]; ``None`` below ``period`` bars."""
    if len(closes) < period:
        return None
    hh = max(highs[-period:])
    ll = min(lows[-period:])
    if hh == ll:
        return _WILLIAMS_FLAT
    return (hh - closes[-1]) / (hh - ll) * _WILLIAMS_SCALE


def choppiness(
    highs: list[float], lows: list[float], closes: list[float], period: int
) -> float | None:
    """Choppiness Index (~0-100); ``None`` below ``period + 1`` bars or flat range."""
    if len(closes) < period + 1:
        return None
    sum_tr = sum(_true_ranges(highs, lows, closes)[-period:])
    rng = max(highs[-period:]) - min(lows[-period:])
    if rng == 0.0 or sum_tr == 0.0:
        return None
    return _STOCH_SCALE * log10(sum_tr / rng) / log10(period)
