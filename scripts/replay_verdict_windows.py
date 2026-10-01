"""EXP-014's evaluation blocks: calendar years and the two halves of the window (S250).

Agent: tooling
Role: cut an arm's points so each session pair falls in exactly one block.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING

from agents.provider.domain.market_calendar import is_trading_session

if TYPE_CHECKING:
    from collections.abc import Sequence

    from scripts.replay_verdict_stats import Point


@dataclass(frozen=True)
class Window:
    """A block of points: its pairs are the consecutive points inside it."""

    label: str
    partial: bool
    points: tuple[Point, ...]


def year_windows(points: Sequence[Point]) -> list[Window]:
    """One window per calendar year; a pair belongs to the year of its later session.

    Each year's window starts at the last point of the year before (its anchor), so
    the years chain to the whole window. A year is partial when the window does not
    hold every pair whose later session falls in it: the year the window starts in
    (the pair arriving on the first point is outside it), and a year the window
    ends in before its last session. The start needs no calendar; the end asks the
    provider's, whose pre-2024 weekday fallback still finds 31 December or the
    weekday before it, on which NYSE has always traded.
    """
    ordered = sorted(points)
    start, end = ordered[0][0], ordered[-1][0]
    windows: list[Window] = []
    for year in sorted({point[0].year for point in ordered[1:]}):
        inside = [index for index, point in enumerate(ordered) if point[0].year == year]
        block = tuple(ordered[max(inside[0] - 1, 0) : inside[-1] + 1])
        partial = start.year == year or (end.year == year and end < _last_session(year))
        windows.append(Window(str(year), partial, block))
    return windows


def half_windows(points: Sequence[Point]) -> list[Window]:
    """The window's two halves by session pairs; the middle point is shared."""
    ordered = tuple(sorted(points))
    middle = (len(ordered) - 1) // 2
    halves = (("first half", ordered[: middle + 1]), ("second half", ordered[middle:]))
    return [Window(label, False, block) for label, block in halves]


def _last_session(year: int) -> date:
    day = date(year, 12, 31)
    while not is_trading_session(day):
        day -= timedelta(days=1)
    return day
