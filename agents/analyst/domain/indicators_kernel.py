"""Pure-Python kernel smoother and calendar signal (NW estimate, turnaround).

Agent: analyst
Role: compute the Nadaraya-Watson deviation and Monday turnaround flag; no numpy.
External I/O: none.
"""

from __future__ import annotations

from math import exp
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

_NW_MIN_BARS = 10
_TURNAROUND_MIN_BARS = 3
_MONDAY, _FRIDAY = 0, 4
_FRIDAY_LOOKBACK = 4


def nadaraya_watson(
    closes: list[float], bandwidth: float, lookback: int
) -> float | None:
    """Percent deviation of the last close from the smoothed line; ``None`` below 10."""
    n = min(lookback, len(closes))
    if n < _NW_MIN_BARS:
        return None
    prices = closes[-n:]
    target = n - 1
    weights = [exp(-0.5 * ((i - target) / bandwidth) ** 2) for i in range(n)]
    wsum = sum(weights)
    if wsum == 0.0:  # pragma: no cover - defensive; a Gaussian weight is never zero.
        return None
    smoothed = sum(w * p for w, p in zip(weights, prices, strict=True)) / wsum
    if smoothed == 0.0:
        return None
    return (prices[-1] - smoothed) / smoothed * 100.0


def turnaround_signal(closes: list[float], dates: list[date]) -> bool | None:
    """Monday-after-weak-Friday flag; always-emit at >=3 bars (``None`` only below)."""
    if len(closes) < _TURNAROUND_MIN_BARS:
        return None
    if dates[-1].weekday() != _MONDAY:
        return False
    last_index = len(dates) - 1
    for offset in range(1, _FRIDAY_LOOKBACK + 1):
        index = last_index - offset
        if index < 0:
            break
        if dates[index].weekday() == _FRIDAY:
            return closes[-1] < closes[index]
    return False
