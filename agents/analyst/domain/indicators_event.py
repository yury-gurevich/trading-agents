"""Pure-Python volume/event indicators (OBV, golden cross).

Agent: analyst
Role: compute OBV vs its signal and the SMA-50/200 golden cross; no I/O, no pandas.
External I/O: none.
"""

from __future__ import annotations


def obv(
    closes: list[float], volumes: list[float], signal_period: int
) -> tuple[float, float] | None:
    """On-balance volume and its signal line; ``None`` below ``signal_period + 1``.

    The OBV series starts at ``0.0`` and adds ``volume[i]`` when the close rises,
    subtracts it when the close falls, and carries forward on an unchanged close.
    The signal is the mean of the last ``signal_period`` OBV values.
    """
    if len(closes) < signal_period + 1:
        return None
    series = [0.0]
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            series.append(series[-1] + volumes[i])
        elif closes[i] < closes[i - 1]:
            series.append(series[-1] - volumes[i])
        else:
            series.append(series[-1])
    signal = sum(series[-signal_period:]) / signal_period
    return series[-1], signal


def golden_cross(closes: list[float], short: int, long: int) -> bool | None:
    """``True`` when the short SMA sits above the long SMA; ``None`` below ``long``."""
    if len(closes) < long:
        return None
    short_sma = sum(closes[-short:]) / short
    long_sma = sum(closes[-long:]) / long
    return short_sma > long_sma
