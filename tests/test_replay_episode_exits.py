"""Planner-review tests: a held line exits when its episode's bars end, not the cache's.

Agent: tooling
Role: prove ended-line exits follow membership episodes, and name their reason plainly.
External I/O: none.

Eleven lines hold more than one membership episode; eight leave the index for 579 to
3,487 days (SNDK 2016-05-12 -> 2025-11-28). Exiting only when a line's last bar in the
whole cache has passed would carry such a holding at a frozen price for years, and
would sell every current member on the cache's final session (DL-234 amendment).
"""

from __future__ import annotations

from datetime import date

from scripts.replay_broker import ReplayPosition
from scripts.replay_marks import exit_ended_positions, mark_positions
from scripts.sp500_bars import BarRow
from scripts.sp500_membership import Episode


def _bar(line: str, day: date, close: float) -> BarRow:
    return BarRow(line, line, day, close, close, close, close, 10)


def _held(line: str, day: date) -> ReplayPosition:
    return ReplayPosition(line, 2, 1_000, 900, day, day)


def test_a_line_leaving_the_index_exits_at_its_episode_end_not_years_later() -> None:
    """S235-A8: re-entry years later does not carry the holding across the gap."""
    out, back = date(2020, 1, 3), date(2023, 1, 3)
    line_bars = {
        "RRR": (_bar("RRR", date(2020, 1, 2), 10), _bar("RRR", out, 12)),
        "ZZZ": (_bar("ZZZ", out, 5), _bar("ZZZ", back, 5)),
    }
    line_bars["RRR"] += (_bar("RRR", back, 40),)
    episodes = (
        Episode("RRR", "RRR", date(2019, 1, 2), out),
        Episode("RRR", "RRR", back, back),
        Episode("ZZZ", "ZZZ", date(2019, 1, 2), back),
    )
    positions = {"RRR": _held("RRR", date(2020, 1, 2))}
    fills: list[dict[str, object]] = []

    result = exit_ended_positions(out, positions, line_bars, episodes, fills)

    assert (result.membership_end_exits, result.data_end_exits) == (1, 0)
    assert fills == [
        {
            "date": "2020-01-03",
            "line": "RRR",
            "side": "sell",
            "quantity": 2,
            "price_cents": 1_200,
            "reason": "membership_end",
        }
    ]
    assert positions == {}


def test_bars_ending_before_the_episode_exit_as_data_end() -> None:
    """S235-A8: a deal closing before the removal date ends the data, not membership."""
    last = date(2020, 1, 3)
    line_bars = {"DDD": (_bar("DDD", date(2020, 1, 2), 10), _bar("DDD", last, 11))}
    episodes = (
        Episode("DDD", "DDD", date(2019, 1, 2), date(2020, 1, 8)),
        Episode("END", "END", date(2019, 1, 2), date(2020, 2, 3)),
    )
    positions = {"DDD": _held("DDD", date(2020, 1, 2))}
    fills: list[dict[str, object]] = []

    result = exit_ended_positions(last, positions, line_bars, episodes, fills)

    assert (result.membership_end_exits, result.data_end_exits) == (0, 1)
    assert [row["reason"] for row in fills] == ["data_end"]


def test_a_current_member_is_not_sold_on_the_caches_final_session() -> None:
    """S235-A8: bars that stop because the cache stops are not an ended line."""
    end = date(2020, 1, 3)
    line_bars = {"CCC": (_bar("CCC", date(2020, 1, 2), 10), _bar("CCC", end, 11))}
    episodes = (Episode("CCC", "CCC", date(2019, 1, 2), end),)
    positions = {"CCC": _held("CCC", date(2020, 1, 2))}
    fills: list[dict[str, object]] = []

    result = exit_ended_positions(end, positions, line_bars, episodes, fills)

    assert (result.membership_end_exits, result.data_end_exits, fills) == (0, 0, [])
    assert "CCC" in positions


def test_a_gap_inside_an_episode_is_carried_not_exited() -> None:
    """S235-A8: a missing bar with more bars to come in the episode is a gap mark."""
    line_bars = {
        "GGG": (_bar("GGG", date(2020, 1, 2), 10), _bar("GGG", date(2020, 1, 7), 12)),
        "END": (_bar("END", date(2020, 1, 9), 1),),
    }
    episodes = (
        Episode("GGG", "GGG", date(2019, 1, 2), date(2020, 1, 9)),
        Episode("END", "END", date(2019, 1, 2), date(2020, 1, 9)),
    )
    positions = {"GGG": _held("GGG", date(2020, 1, 2))}
    fills: list[dict[str, object]] = []

    exits = exit_ended_positions(
        date(2020, 1, 2), positions, line_bars, episodes, fills
    )
    marked = mark_positions(0, positions, line_bars, date(2020, 1, 3))

    assert (exits.membership_end_exits, exits.data_end_exits, fills) == (0, 0, [])
    assert (marked.long_cents, marked.gap_marks) == (2_000, 1)
