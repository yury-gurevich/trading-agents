"""The NYSE calendar holds every full-day closure from 2016 (S250 return 1, DL-258).

Agent: provider
Role: pin the per-year session counts 2016-2025 and every closure the planner measured
      on the replay cache (Return 1's table), so a pre-2024 weekday holiday is never
      counted as a session again.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

import pytest

from agents.provider.domain.market_calendar import (
    calendar_window_end,
    is_trading_session,
    trading_sessions_between,
)

# Sessions a year, NYSE's record (Return 1): what the replay cache holds, 2016-2025.
SESSIONS_A_YEAR = {
    2016: 252,
    2017: 251,
    2018: 251,
    2019: 252,
    2020: 253,
    2021: 252,
    2022: 251,
    2023: 250,
    2024: 252,
    2025: 250,
}

# Return 1's closures (MM-DD): every weekday 2016-01-04..2026-09-25 that is not a
# session in the cache, plus 2016-01-01 from the public record.
_CLOSURES = {
    2016: "01-01 01-18 02-15 03-25 05-30 07-04 09-05 11-24 12-26",
    2017: "01-02 01-16 02-20 04-14 05-29 07-04 09-04 11-23 12-25",
    2018: "01-01 01-15 02-19 03-30 05-28 07-04 09-03 11-22 12-05 12-25",
    2019: "01-01 01-21 02-18 04-19 05-27 07-04 09-02 11-28 12-25",
    2020: "01-01 01-20 02-17 04-10 05-25 07-03 09-07 11-26 12-25",
    2021: "01-01 01-18 02-15 04-02 05-31 07-05 09-06 11-25 12-24",
    2022: "01-17 02-21 04-15 05-30 06-20 07-04 09-05 11-24 12-26",
    2023: "01-02 01-16 02-20 04-07 05-29 06-19 07-04 09-04 11-23 12-25",
    2025: "01-09",
}
CLOSURES = tuple(
    date(year, int(day[:2]), int(day[3:]))
    for year, days in _CLOSURES.items()
    for day in days.split()
)


@pytest.mark.parametrize(("year", "sessions"), SESSIONS_A_YEAR.items())
def test_each_year_holds_nyses_sessions(year: int, sessions: int) -> None:
    """PROV-TRG-05 / DL-10: a year's sessions are NYSE's count, so a lookback in
    sessions reaches as far back as the exchange actually traded."""
    assert trading_sessions_between(date(year - 1, 12, 31), date(year, 12, 31)) == (
        sessions
    )


@pytest.mark.parametrize("day", CLOSURES, ids=str)
def test_each_measured_closure_is_not_a_session(day: date) -> None:
    """PROV-TRG-05 / DL-10: every weekday closure Return 1 measured is no session."""
    assert day.weekday() < 5
    assert is_trading_session(day) is False


def test_the_table_still_ends_where_it_did() -> None:
    """The repair extends the table backwards only; its covered end is unchanged."""
    assert len(CLOSURES) == 75
    assert calendar_window_end() == date(2027, 12, 31)
