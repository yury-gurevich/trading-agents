"""BarrierHistory contract — the daily history a barrier claim is fitted on.

Agent: contracts
Role: contract — the node the provider (its only writer) writes per AnalystRun
      holding a qualifying buy for the forecaster to read, the edge that links it,
      its key, and the one rule both agents use to say which buys qualify (DL-241
      D10).
External I/O: none.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Literal

from contracts.common import _Frozen

if TYPE_CHECKING:
    from contracts.analyst import Recommendation, RecommendationSet

BARRIER_HISTORY_LABEL = "BarrierHistory"
#: AnalystRun -BARRIER_HISTORY_BY-> BarrierHistory.
BARRIER_HISTORY_EDGE = "BARRIER_HISTORY_BY"

#: One daily bar as stored: (ISO date, open, high, low, close).
BarRow = tuple[str, float, float, float, float]


class TickerHistory(_Frozen):
    bars: tuple[BarRow, ...]
    """The last <= ``sessions_requested`` daily bars, oldest first."""
    bar_count: int


class BarrierHistory(_Frozen):
    analyst_run_key: str
    status: Literal["ok", "failed"]
    reason: str | None = None
    """Why the fetch failed (status ``failed``); None when it succeeded."""
    window_start: date
    window_end: date
    sessions_requested: int
    requested: tuple[str, ...]
    histories: dict[str, TickerHistory]
    dropped: dict[str, str]
    """Ticker -> the named reason it has no history here; never silently absent."""
    stale: tuple[str, ...] = ()
    """Served tickers whose last bar is older than the provider's staleness limit."""
    created_at: datetime


def barrier_history_key(analyst_run_key: str) -> str:
    """The BarrierHistory key for one AnalystRun: one node per run."""
    return f"barrier-history:{analyst_run_key}"


def barrier_buys(recommendation_set: RecommendationSet) -> tuple[Recommendation, ...]:
    """Buys carrying both a suggested stop and a suggested target, in run order."""
    return tuple(
        recommendation
        for recommendation in recommendation_set.recommendations
        if recommendation.action == "buy"
        and recommendation.suggested_stop_pct is not None
        and recommendation.suggested_target_pct is not None
    )
