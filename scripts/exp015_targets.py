"""EXP-015's forward returns, session d+1's open to d+h's close, and masks (S289).

Agent: tooling
Role: give each line bar its raw forward return at each horizon, SPY's over the
      same sessions, and the bars whose windows span a known adjustment error.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from scripts.exp015_spec import FEATURE_LOOKBACK, HORIZONS

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from datetime import date


def forward_returns(
    dates: Sequence[date],
    opens: np.ndarray,
    closes: np.ndarray,
    session_index: dict[date, int],
    sessions: Sequence[date],
) -> np.ndarray:
    """(bars x horizons) raw returns; NaN unless the line has a bar on both sessions."""
    position = {day: i for i, day in enumerate(dates)}
    out = np.full((len(dates), len(HORIZONS)), np.nan)
    for i, day in enumerate(dates):
        j = session_index[day]
        entry = position.get(sessions[j + 1]) if j + 1 < len(sessions) else None
        for k, horizon in enumerate(HORIZONS):
            if entry is None or j + horizon >= len(sessions):
                continue
            exit_ = position.get(sessions[j + horizon])
            if exit_ is not None:
                out[i, k] = closes[exit_] / opens[entry] - 1.0
    return out


def adjustment_masks(
    dates: Sequence[date], moves: Iterable[date], session_index: dict[date, int]
) -> tuple[np.ndarray, np.ndarray]:
    """(features masked, targets masked) per bar, for the line's adjustment-error dates.

    A bar's features read FEATURE_LOOKBACK sessions back; its targets read the next
    max(HORIZONS) sessions: a move inside either window masks it (DL-313 D5).
    """
    features = np.zeros(len(dates), dtype=bool)
    targets = np.zeros(len(dates), dtype=bool)
    longest = max(HORIZONS)
    for move in moves:
        m = session_index[move]
        for i, day in enumerate(dates):
            j = session_index[day]
            features[i] |= m <= j <= m + FEATURE_LOOKBACK
            targets[i] |= j < m <= j + longest
    return features, targets
