"""NYSE trading-session calendar for the staleness gate.

Agent: provider
Role: count trading sessions between two dates (weekends + NYSE holidays excluded),
      so data staleness is measured in sessions - not calendar days - matching the
      stated intent of provider `max_staleness_days` (DL-10).
External I/O: none.

The holiday set is a static list of full-day NYSE closures (2016-2027), kept
dependency-free on purpose; 2016-2023 and 2025-01-09 were added in S250 return 1
(DL-258), measured against the replay cache. Dates beyond the window fall back to
weekday counting (slightly conservative). When the window needs extending or
per-exchange precision, swap in a market-calendar library (e.g. exchange_calendars /
pandas-market-calendars).
"""

from __future__ import annotations

from datetime import date, timedelta

# Full-day NYSE closures (observed dates). Early-close days are still sessions and
# are intentionally not modeled.
_NYSE_HOLIDAYS: frozenset[date] = frozenset(
    {
        # 2016
        date(2016, 1, 1),
        date(2016, 1, 18),
        date(2016, 2, 15),
        date(2016, 3, 25),
        date(2016, 5, 30),
        date(2016, 7, 4),
        date(2016, 9, 5),
        date(2016, 11, 24),
        date(2016, 12, 26),
        # 2017
        date(2017, 1, 2),
        date(2017, 1, 16),
        date(2017, 2, 20),
        date(2017, 4, 14),
        date(2017, 5, 29),
        date(2017, 7, 4),
        date(2017, 9, 4),
        date(2017, 11, 23),
        date(2017, 12, 25),
        # 2018
        date(2018, 1, 1),
        date(2018, 1, 15),
        date(2018, 2, 19),
        date(2018, 3, 30),
        date(2018, 5, 28),
        date(2018, 7, 4),
        date(2018, 9, 3),
        date(2018, 11, 22),
        date(2018, 12, 5),  # national day of mourning (President Bush)
        date(2018, 12, 25),
        # 2019
        date(2019, 1, 1),
        date(2019, 1, 21),
        date(2019, 2, 18),
        date(2019, 4, 19),
        date(2019, 5, 27),
        date(2019, 7, 4),
        date(2019, 9, 2),
        date(2019, 11, 28),
        date(2019, 12, 25),
        # 2020
        date(2020, 1, 1),
        date(2020, 1, 20),
        date(2020, 2, 17),
        date(2020, 4, 10),
        date(2020, 5, 25),
        date(2020, 7, 3),
        date(2020, 9, 7),
        date(2020, 11, 26),
        date(2020, 12, 25),
        # 2021
        date(2021, 1, 1),
        date(2021, 1, 18),
        date(2021, 2, 15),
        date(2021, 4, 2),
        date(2021, 5, 31),
        date(2021, 7, 5),
        date(2021, 9, 6),
        date(2021, 11, 25),
        date(2021, 12, 24),
        # 2022
        date(2022, 1, 17),
        date(2022, 2, 21),
        date(2022, 4, 15),
        date(2022, 5, 30),
        date(2022, 6, 20),
        date(2022, 7, 4),
        date(2022, 9, 5),
        date(2022, 11, 24),
        date(2022, 12, 26),
        # 2023
        date(2023, 1, 2),
        date(2023, 1, 16),
        date(2023, 2, 20),
        date(2023, 4, 7),
        date(2023, 5, 29),
        date(2023, 6, 19),
        date(2023, 7, 4),
        date(2023, 9, 4),
        date(2023, 11, 23),
        date(2023, 12, 25),
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
        date(2025, 1, 9),  # national day of mourning (President Carter)
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


def calendar_window_end() -> date:
    """Return the final calendar date covered by the explicit holiday table."""
    return date(max(day.year for day in _NYSE_HOLIDAYS), 12, 31)


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
