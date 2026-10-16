"""What an EXP-022 arm's exits did: round trips by the reason that closed them (S282).

Agent: tooling
Role: pair each sell in an arm's fills.csv with the oldest open buy of its line, and
      summarise the trips by exit reason. Reported beside the verdict, never in it.
External I/O: reads one arm's fills.csv.
"""

from __future__ import annotations

import csv
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import date
from statistics import median
from typing import TYPE_CHECKING, Any

from scripts.replay_verdict_stats import SESSIONS_PER_YEAR

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

_PERCENT = 100.0


@dataclass(frozen=True)
class Trip:
    """One buy and the sell that closed it."""

    reason: str
    held_sessions: int
    return_pct: float


def exit_profile(fills_csv: Path, sessions: Sequence[date]) -> dict[str, Any]:
    """Buys, buys a year, trips by exit reason, lines open at the end, stray sells."""
    with fills_csv.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return profile_of(rows, sessions)


def profile_of(
    rows: Sequence[dict[str, str]], sessions: Sequence[date]
) -> dict[str, Any]:
    """The profile of fill rows in their file order; each fill's date is a session."""
    index = {day: position for position, day in enumerate(sessions)}
    opened: dict[str, deque[tuple[int, int]]] = defaultdict(deque)
    trips: list[Trip] = []
    buys = unmatched = 0
    for row in rows:
        session = index[date.fromisoformat(row["date"])]
        price = int(row["price_cents"])
        if row["side"] == "buy":
            buys += 1
            opened[row["line"]].append((session, price))
            continue
        queue = opened.get(row["line"])
        if not queue:
            unmatched += 1
            continue
        start, cost = queue.popleft()
        gain = (price / cost - 1.0) * _PERCENT
        trips.append(Trip(row["reason"], session - start, gain))
    years = max(len(sessions) - 1, 1) / SESSIONS_PER_YEAR
    by_reason: dict[str, list[Trip]] = defaultdict(list)
    for trip in trips:
        by_reason[trip.reason].append(trip)
    return {
        "buys": buys,
        "buys_per_year": buys / years,
        "exits": {reason: _summary(by_reason[reason]) for reason in sorted(by_reason)},
        "open_at_end": sum(len(queue) for queue in opened.values()),
        "trips": len(trips),
        "unmatched_sells": unmatched,
    }


def _summary(trips: Sequence[Trip]) -> dict[str, Any]:
    gains = sum(1 for trip in trips if trip.return_pct > 0)
    return {
        "count": len(trips),
        "gain_share_pct": gains / len(trips) * _PERCENT,
        "mean_return_pct": sum(trip.return_pct for trip in trips) / len(trips),
        "median_held_sessions": float(median(trip.held_sessions for trip in trips)),
    }
