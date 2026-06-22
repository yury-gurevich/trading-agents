"""NYSE trading-session calendar for the staleness gate.

Agent: provider
Role: count trading sessions between two dates (weekends + NYSE holidays excluded),
      so data staleness is measured in sessions - not calendar days - matching the
      stated intent of provider `max_staleness_days` (DL-10).
External I/O: none.

The holiday set is a static list of full-day NYSE closures (2024-2027), kept
dependency-free on purpose. Dates beyond the window fall back to weekday counting
(slightly conservative). When the window needs extending or per-exchange precision,
swap in a market-calendar library (e.g. exchange_calendars / pandas-market-calendars).
"""

from __future__ import annotations

from datetime import date, timedelta

# Full-day NYSE closures (observed dates). Early-close days are still sessions and
# are intentionally not modeled.
_NYSE_HOLIDAYS: frozenset[date] = frozenset(
    {
        # 2024
        date(2024, 1, 1),
        date(2024, 1, 15),
        date(2024, 2, 19),
        date(2024, 3, 29),
        date(2024, 5, 27),
        date(2024, 6, 19),
        date(2024, 7, 4),
        date(2024, 9, 2),
        date(2024, 11, 28),
        date(2024, 12, 25),
        # 2025
        date(2025, 1, 1),
        date(2025, 1, 20),
        date(2025, 2, 17),
        date(2025, 4, 18),
        date(2025, 5, 26),
        date(2025, 6, 19),
        date(2025, 7, 4),
        date(2025, 9, 1),
        date(2025, 11, 27),
        date(2025, 12, 25),
        # 2026
        date(2026, 1, 1),
        date(2026, 1, 19),
        date(2026, 2, 16),
        date(2026, 4, 3),
        date(2026, 5, 25),
        date(2026, 6, 19),
        date(2026, 7, 3),
        date(2026, 9, 7),
        date(2026, 11, 26),
        date(2026, 12, 25),
        # 2027
        date(2027, 1, 1),
        date(2027, 1, 18),
        date(2027, 2, 15),
        date(2027, 3, 26),
        date(2027, 5, 31),
        date(2027, 6, 18),
        date(2027, 7, 5),
        date(2027, 9, 6),
        date(2027, 11, 25),
        date(2027, 12, 24),
    }
)


def is_trading_session(day: date) -> bool:
    """True when *day* is a NYSE trading session (a weekday that is not a holiday)."""
    return day.weekday() < 5 and day not in _NYSE_HOLIDAYS


def trading_sessions_between(after: date, through: date) -> int:
    """Count NYSE trading sessions ``d`` with ``after < d <= through``.

    Zero when *through* is on or before *after*. Read as: how many sessions old the
    latest bar (*after*) is relative to the window end (*through*).
    """
    count = 0
    day = after + timedelta(days=1)
    while day <= through:
        if is_trading_session(day):
            count += 1
        day += timedelta(days=1)
    return count
