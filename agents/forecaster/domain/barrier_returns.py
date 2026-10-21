"""Barrier returns, pure: what a claim's own paths say of its return and its timing.

Agent: forecaster
Role: from the paths a claim's three probabilities were counted on (DL-312), state the
      mean return to the first barrier or the tenth close (the stop's return at the
      stop, the target's at the target, else the tenth close's), the tenth close's 5th
      percentile with the barriers ignored, and the median session of each barrier's
      first touch. A first touch is EXP-018's: the low is checked first, so a session
      touching both is the stop. Never a second simulation: the figures read the
      probabilities' own paths.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from agents.forecaster.domain.barrier_garch import HORIZON_SESSIONS

if TYPE_CHECKING:
    from numpy.typing import NDArray

    Floats = NDArray[np.float64]

#: The worst case is the tenth close's return one path in twenty falls below.
TAIL_PERCENTILE = 5


@dataclass(frozen=True)
class BarrierReturns:
    """A claim's return figures, each a fraction of the claim's close."""

    expected_return: float
    """The mean return to the first barrier or the tenth close."""
    close_return_p05: float
    """The tenth close's return at its 5th percentile, the barriers ignored."""
    sessions_to_target: float | None
    """The median session (1 to 10) of the target's first touch; None if none."""
    sessions_to_stop: float | None
    """The median session (1 to 10) of the stop's first touch; None if none."""


def barrier_returns(
    paths: tuple[Floats, Floats, Floats, Floats], stop: float, target: float
) -> BarrierReturns:
    """The figures of ``paths`` (`garch_paths`' four arrays) for one stop and target."""
    prev, high, low, last = paths
    hit_s = prev * low <= 1 - stop
    hit_t = prev * high >= 1 + target
    fs = np.where(hit_s.any(1), hit_s.argmax(1), HORIZON_SESSIONS)
    ft = np.where(hit_t.any(1), hit_t.argmax(1), HORIZON_SESSIONS)
    stop_first = (fs < HORIZON_SESSIONS) & (fs <= ft)
    target_first = (ft < HORIZON_SESSIONS) & (ft < fs)
    close_return = last - 1
    returns = np.where(stop_first, -stop, np.where(target_first, target, close_return))
    return BarrierReturns(
        expected_return=float(returns.mean()),
        close_return_p05=float(np.percentile(close_return, TAIL_PERCENTILE)),
        sessions_to_target=_median_session(ft, target_first),
        sessions_to_stop=_median_session(fs, stop_first),
    )


def _median_session(
    first: NDArray[np.int64], touched: NDArray[np.bool_]
) -> float | None:
    """The median 1-based session of the touched paths' first touch, or None."""
    if not touched.any():
        return None
    return float(np.median(first[touched] + 1))
