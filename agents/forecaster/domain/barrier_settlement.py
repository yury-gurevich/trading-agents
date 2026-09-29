"""Barrier settlement, pure: what the market did to a claim's stop and target.

Agent: forecaster
Role: settle one claim on one ticker's later daily bars by EXP-018's outcome rule
      (`scripts/barrier_testbed.outcome()`, copied: over the 10 sessions after
      ``as_of`` the low is checked first, so a session touching both is the stop),
      measured from the settling series' own close on ``as_of``; or void it with a
      named reason, never a false outcome (S241, DL-243). It reads the claim's date,
      entry close and barriers only: never its probabilities, which only the Brier
      uses.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from typing import TYPE_CHECKING, NamedTuple

import numpy as np

from agents.forecaster.domain.barrier_garch import HORIZON_SESSIONS

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import date

#: EXP-018's outcomes, in the index order `outcome()` returns and Brier scores use.
OUTCOMES = ("stop", "target", "neither")
VOID = "void"
#: The bars are raw, so a split reads as a one-day crash: a session-over-session
#: close ratio below 0.6 or above 1.67 (a move of 40 % or more, in large caps a
#: corporate action) voids the claim (S241 spec, Scope 3).
CORPORATE_ACTION = "suspected_corporate_action"
CORPORATE_ACTION_LOW = 0.6
CORPORATE_ACTION_HIGH = 1.67
#: A claim still open this many calendar days after its as_of is void: its ticker
#: left the universe, or its bars never came (S241 spec, Scope 3).
NO_SETTLING_BARS = "no_settling_bars"
NO_SETTLING_BARS_DAYS = 45


class SettlingBar(NamedTuple):
    """One daily bar of the settling series, as the settlement reads it."""

    day: date
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class Settlement:
    """What a claim settled to, and what it was measured from."""

    outcome: str
    """``stop``, ``target``, ``neither`` or ``void``."""
    void_reason: str | None
    settled_on: date
    """The tenth session's date, or, for a void, the date of the pass that voided it."""
    entry_close_settling: float | None
    """The settling series' own close on ``as_of`` (absent when it has no such bar)."""
    entry_ratio: float | None
    """``entry_close_settling`` / the claim's ``entry_close``: drift between fetches."""


def outcome_index(
    hi: Sequence[float],
    lo: Sequence[float],
    cl: Sequence[float],
    t: int,
    stop: float,
    target: float,
) -> int:
    """0 stop first, 1 target first, 2 neither; touching both counts as the stop.

    `scripts/barrier_testbed.outcome()` line for line, with its ``H`` as
    ``HORIZON_SESSIONS``: the same comparisons in the same order.
    """
    for k in range(t + 1, t + HORIZON_SESSIONS + 1):
        if lo[k] <= cl[t] * (1 - stop):
            return 0
        if hi[k] >= cl[t] * (1 + target):
            return 1
    return 2


def settle(
    bars: Sequence[SettlingBar],
    *,
    as_of: date,
    entry_close: float,
    stop_pct: float,
    target_pct: float,
    pass_date: date,
) -> Settlement | None:
    """Settle a claim on ``bars`` (one ticker, oldest first), or ``None``: still open.

    The claim stays open while the series lacks the ``as_of`` bar or holds fewer
    than 10 sessions after it, until ``pass_date`` is 45 or more days after
    ``as_of``, when it is void (``no_settling_bars``).
    """
    t = next((i for i, bar in enumerate(bars) if bar.day == as_of), None)
    if t is None or len(bars) - 1 - t < HORIZON_SESSIONS:
        if (pass_date - as_of).days >= NO_SETTLING_BARS_DAYS:
            return Settlement(VOID, NO_SETTLING_BARS, pass_date, None, None)
        return None
    window = bars[t : t + HORIZON_SESSIONS + 1]
    entry = window[0].close
    ratio = entry / entry_close
    if _corporate_action(window):
        return Settlement(VOID, CORPORATE_ACTION, pass_date, entry, ratio)
    k = outcome_index(
        [bar.high for bar in window],
        [bar.low for bar in window],
        [bar.close for bar in window],
        0,
        stop_pct,
        target_pct,
    )
    return Settlement(OUTCOMES[k], None, window[-1].day, entry, ratio)


def _corporate_action(window: Sequence[SettlingBar]) -> bool:
    """Whether any session-over-session raw close ratio leaves [0.6, 1.67]."""
    return any(
        not CORPORATE_ACTION_LOW <= later.close / earlier.close <= CORPORATE_ACTION_HIGH
        for earlier, later in pairwise(window)
    )


def brier(probabilities: Sequence[float], outcome: str) -> float:
    """The claim's three-class Brier: squared distance from the realised outcome.

    EXP-018's ``((P - Y) ** 2).sum(1)`` for one case.
    """
    realised = np.eye(3)[OUTCOMES.index(outcome)]
    return float(((np.asarray(probabilities, dtype=float) - realised) ** 2).sum())
