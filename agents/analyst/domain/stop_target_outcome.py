"""Realized adverse excursion behind a stop/target proposal.

Agent: analyst
Role: measure how far a name actually fell after a recommendation, over a window
      that has fully settled, so a stop width can be judged against this book.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import date

    from contracts.provider import OHLCVBar

FAVORABLE_EXCURSION_PCT = "favorable_excursion_pct"
FAVORABLE_EXCURSION_HORIZON_DAYS = "favorable_excursion_horizon_days"
FAVORABLE_EXCURSION_SAMPLE_COUNT = "favorable_excursion_sample_count"
FAVORABLE_EXCURSION_LOOKBACK_WINDOWS = "favorable_excursion_lookback_windows"


@dataclass(frozen=True)
class DrawdownObservation:
    """A settled adverse excursion together with the horizon it covers."""

    drawdown_pct: float
    horizon_days: int


@dataclass(frozen=True)
class FavorableExcursionEstimate:
    """A decision-time upside estimate and the prior windows behind it."""

    excursion_pct: float
    horizon_days: int
    sample_count: int


def observed_drawdown(
    bars: Sequence[OHLCVBar], decision_day: date, horizon_days: int
) -> DrawdownObservation | None:
    """Return the settled drawdown after ``decision_day``, or ``None`` if unsettled.

    The measurement is the deepest close-to-low fall over the ``horizon_days``
    sessions **following** the decision bar, as a fraction of the decision close.
    ``None`` means the window has not settled or the anchor bar is missing - never
    that the name did not fall (`ANLZ-OBS-05`).
    """
    if horizon_days < 1:
        return None
    ordered = sorted(bars, key=lambda bar: bar.bar_date)
    anchor = _anchor(ordered, decision_day)
    if anchor is None:
        return None
    after = [bar for bar in ordered if bar.bar_date > anchor.bar_date]
    if len(after) < horizon_days:
        return None
    worst = min(bar.low for bar in after[:horizon_days])
    return DrawdownObservation(
        drawdown_pct=max((anchor.close - worst) / anchor.close, 0.0),
        horizon_days=horizon_days,
    )


def trailing_favorable_excursion(
    bars: Sequence[OHLCVBar],
    decision_day: date,
    horizon_days: int,
    lookback_windows: int,
) -> FavorableExcursionEstimate | None:
    """Return median prior close-to-high upside, or None when unavailable.

    Every sampled window ends on or before ``decision_day``. The realised
    drawdown backfill looks forward from the recommendation; this estimate
    looks backward over already-fetched bars and therefore stays decision-time.
    """
    if horizon_days < 1 or lookback_windows < 1:
        return None
    ordered = sorted(bars, key=lambda bar: bar.bar_date)
    anchor = _anchor(ordered, decision_day)
    if anchor is None:
        return None
    decision_index = ordered.index(anchor)
    latest_start = decision_index - horizon_days
    if latest_start < 0:
        return None
    first_start = max(0, latest_start - lookback_windows + 1)
    excursions = [
        _favorable_window(ordered[index], ordered[index + 1 : index + 1 + horizon_days])
        for index in range(first_start, latest_start + 1)
    ]
    return FavorableExcursionEstimate(
        excursion_pct=median(excursions),
        horizon_days=horizon_days,
        sample_count=len(excursions),
    )


def _anchor(ordered: Sequence[OHLCVBar], decision_day: date) -> OHLCVBar | None:
    settled = [bar for bar in ordered if bar.bar_date <= decision_day]
    return settled[-1] if settled else None


def _favorable_window(anchor: OHLCVBar, window: Sequence[OHLCVBar]) -> float:
    best = max(bar.high for bar in window)
    return max((best - anchor.close) / anchor.close, 0.0)
