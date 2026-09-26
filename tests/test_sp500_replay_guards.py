"""Tests for S233 replay switch and known-move guards.

Agent: tooling
Role: verify suspicious replay price moves are named or refused.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pytest
from scripts.sp500_bars import BarRow
from scripts.sp500_chain import SwitchRecord
from scripts.sp500_guards import (
    KnownMove,
    require_switch_actions,
    review_same_source_moves,
)
from scripts.sp500_membership import Episode

if TYPE_CHECKING:
    from pathlib import Path


def test_hard_switch_requires_named_action() -> None:
    """S233-A6: an undeclared hard switch fails and a named action passes."""
    missing = (
        SwitchRecord(
            "UAA",
            "UA",
            "UAA",
            date(2016, 4, 7),
            date(2016, 4, 8),
            -0.489,
            -0.489,
            "",
        ),
    )
    with pytest.raises(SystemExit, match="UAA UA->UAA 2016-04-08"):
        require_switch_actions(missing)

    require_switch_actions(
        (
            SwitchRecord(
                "UAA",
                "UA",
                "UAA",
                date(2016, 4, 7),
                date(2016, 4, 8),
                -0.489,
                -0.489,
                "class C share dividend",
            ),
        )
    )


def test_unlisted_big_same_source_move_fails_and_listed_passes() -> None:
    """S233-A7: an unlisted big same-source move fails by line and date."""
    first, second = date(2016, 5, 13), date(2016, 5, 16)
    rows = (
        BarRow("SW", "SW", first, 100.0, 100.0, 100.0, 100.0),
        BarRow("SW", "SW", second, 15.0, 15.0, 15.0, 15.0),
    )
    spy = {first: 100.0, second: 101.0}
    episodes = _one_episode("SW", first, second)

    with pytest.raises(SystemExit, match="SW SW 2016-05-16"):
        review_same_source_moves(rows, spy, (), episodes)

    reviewed = review_same_source_moves(
        rows,
        spy,
        (KnownMove("SW", second, "adjustment-error", "synthetic guard proof"),),
        episodes,
    )

    assert [(row.line, row.date, row.kind) for row in reviewed] == [
        ("SW", second, "adjustment-error")
    ]


def test_move_under_review_limit_is_not_reviewed() -> None:
    """S233-A8: a same-source move under the review limit is not listed."""
    first, second = date(2020, 1, 1), date(2020, 1, 2)
    rows = (
        BarRow("CALM", "CALM", first, 100.0, 100.0, 100.0, 100.0),
        BarRow("CALM", "CALM", second, 52.0, 52.0, 52.0, 52.0),
    )

    spy = {first: 100.0, second: 101.0}
    episodes = _one_episode("CALM", first, second)

    assert review_same_source_moves(rows, spy, (), episodes) == ()


def test_move_across_an_episode_gap_is_not_a_move() -> None:
    """S233-A7: only sessions inside one episode are compared (FSLR, 2026-09-26)."""
    out, entry, after = date(2017, 3, 17), date(2022, 12, 19), date(2022, 12, 20)
    rows = (
        BarRow("FSLR", "FSLR", out, 30.0, 30.0, 30.0, 30.0),
        BarRow("FSLR", "FSLR", entry, 150.0, 150.0, 150.0, 150.0),
        BarRow("FSLR", "FSLR", after, 20.0, 20.0, 20.0, 20.0),
    )
    spy = {out: 100.0, entry: 100.0, after: 100.0}
    episodes = (
        Episode("FSLR", "FSLR", date(2016, 1, 4), out),
        Episode("FSLR", "FSLR", entry, date(2026, 9, 24)),
    )
    with pytest.raises(SystemExit, match=r"same-source move .*: FSLR FSLR 2022-12-20$"):
        review_same_source_moves(rows, spy, (), episodes)


def test_symbol_map_loads_optional_action_column(tmp_path: Path) -> None:
    """S233-A9: map rows load with and without optional `action` values."""
    from scripts.sp500_membership import load_symbol_map

    with_action = tmp_path / "with-action.csv"
    with_action.write_text(
        "kind,line,symbol,from,to,evidence,action\n"
        "bars,NEW,OLD,2020-01-01,2020-01-02,fixture,spin\n",
        encoding="utf-8",
    )
    without_action = tmp_path / "without-action.csv"
    without_action.write_text(
        "kind,line,symbol,from,to,evidence\n"
        "bars,NEW,OLD,2020-01-01,2020-01-02,fixture\n",
        encoding="utf-8",
    )

    assert load_symbol_map(with_action)[0].action == "spin"
    assert load_symbol_map(without_action)[0].action == ""


def test_committed_dlph_row_ends_before_aptv_starts() -> None:
    """S233-A10: the committed DLPH row ends at the measured lineage boundary."""
    from scripts.sp500_membership import load_symbol_map

    rows = {(row.kind, row.line, row.symbol): row for row in load_symbol_map()}

    assert rows[("bars", "APTV", "DLPH")].to_date == date(2017, 11, 16)


def _one_episode(line: str, first: date, last: date) -> tuple[Episode, ...]:
    return (Episode(line, line, first, last),)
