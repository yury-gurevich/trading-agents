"""Tests for S235 replay series slicing.

Agent: tooling
Role: verify session windows avoid lookahead while including the decision day.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

from scripts.replay_series import window_bars
from scripts.sp500_bars import BarRow


def test_window_bars_include_session_but_not_next_session() -> None:
    """S235-A6: decision windows end at d and never include d+1."""
    rows: dict[str, tuple[BarRow, ...]] = {
        "AAA": (
            BarRow("AAA", "AAA", date(2020, 1, 1), 1, 1, 1, 1, 10),
            BarRow("AAA", "AAA", date(2020, 1, 2), 2, 2, 2, 2, 20),
            BarRow("AAA", "AAA", date(2020, 1, 3), 3, 3, 3, 3, 30),
        )
    }

    observed = window_bars(rows, ("AAA",), date(2020, 1, 2), 2)

    assert [row.date for row in observed] == [date(2020, 1, 1), date(2020, 1, 2)]
