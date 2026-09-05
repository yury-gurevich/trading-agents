"""Realized adverse excursion behind a stop/target proposal.

Agent: analyst
Role: measure how far a name actually fell after a recommendation, over a window
      that has fully settled, so a stop width can be judged against this book.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import date

    from contracts.provider import OHLCVBar


@dataclass(frozen=True)
class DrawdownObservation:
    """A settled adverse excursion together with the horizon it covers."""

    drawdown_pct: float
    horizon_days: int


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


def _anchor(ordered: Sequence[OHLCVBar], decision_day: date) -> OHLCVBar | None:
    settled = [bar for bar in ordered if bar.bar_date <= decision_day]
    return settled[-1] if settled else None
