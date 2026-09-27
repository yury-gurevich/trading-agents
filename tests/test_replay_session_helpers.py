"""S237 Part A helpers: held values from the latest visible close.

Agent: tooling
Role: prove the replay values a held line at its last close on or before the session.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from scripts.replay_broker import ReplayPosition
from scripts.replay_session_helpers import position_values
from scripts.sp500_bars import BarRow

from contracts.common import Money

DAY = date(2020, 1, 3)


def _position(line: str) -> ReplayPosition:
    return ReplayPosition(
        line=line,
        quantity=10,
        entry_price_cents=1_000,
        stop_price_cents=950,
        opened=date(2020, 1, 2),
        stop_active_from=DAY,
    )


def test_a_held_line_is_worth_its_latest_visible_close_and_never_a_later_one() -> None:
    """PM-NEV-06 / PM-NEV-08: the book's value never reads a bar after the session."""
    bars = {
        "AAA": (
            BarRow("AAA", "AAA", date(2020, 1, 2), 10, 11, 9, 10.5, 100),
            BarRow("AAA", "AAA", DAY, 10, 11, 9, 11.0, 100),
            BarRow("AAA", "AAA", date(2020, 1, 6), 10, 99, 9, 99.0, 100),
        ),
        "BBB": (BarRow("BBB", "BBB", date(2020, 1, 6), 10, 11, 9, 10.0, 100),),
    }

    values = position_values(
        {"AAA": _position("AAA"), "BBB": _position("BBB")}, bars, DAY
    )

    assert values == {"AAA": Money(amount=Decimal("110.00"))}
