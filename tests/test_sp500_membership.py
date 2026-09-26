"""Tests for S231 point-in-time membership reconstruction.

Agent: tooling
Role: verify current constituents plus dated changes become session membership.
External I/O: none.
"""

from __future__ import annotations

from datetime import date


def test_membership_reconstruction_matches_known_history() -> None:
    """S231-A3: undo-then-replay reconstruction is exact on a known history."""
    from scripts.sp500_membership import reconstruct_membership
    from scripts.sp500_wiki import Change, Constituent

    constituents = [
        Constituent(symbol=symbol, security=f"{symbol} Inc", date_added=None, cik="")
        for symbol in ("AAA", "BBB", "CCC", "DDD", "EEE", "FFF")
    ]
    changes = [
        Change(date(2020, 1, 2), "CCC", "CCC Inc", "XXX", "XXX Inc", "swap 1"),
        Change(date(2020, 1, 3), "DDD", "DDD Inc", "YYY", "YYY Inc", "swap 2"),
        Change(date(2020, 1, 4), "EEE", "EEE Inc", "ZZZ", "ZZZ Inc", "swap 3"),
        Change(date(2020, 1, 5), "FFF", "FFF Inc", "WWW", "WWW Inc", "swap 4"),
    ]
    sessions = [date(2020, 1, day) for day in range(1, 6)]

    result = reconstruct_membership(constituents, changes, sessions, symbol_map=())

    assert result.members_by_session == {
        date(2020, 1, 1): ("AAA", "BBB", "WWW", "XXX", "YYY", "ZZZ"),
        date(2020, 1, 2): ("AAA", "BBB", "CCC", "WWW", "YYY", "ZZZ"),
        date(2020, 1, 3): ("AAA", "BBB", "CCC", "DDD", "WWW", "ZZZ"),
        date(2020, 1, 4): ("AAA", "BBB", "CCC", "DDD", "EEE", "WWW"),
        date(2020, 1, 5): ("AAA", "BBB", "CCC", "DDD", "EEE", "FFF"),
    }
    assert result.count_min == 6
    assert result.count_max == 6
    assert result.unreconciled == ()


def test_rename_row_prevents_double_count() -> None:
    """S231-A4: rename map rows create one line with consecutive ticker episodes."""
    from scripts.sp500_membership import SymbolMapRow, reconstruct_membership
    from scripts.sp500_wiki import Change, Constituent

    constituents = [
        Constituent(symbol="KEEP", security="Keep", date_added=None, cik=""),
        Constituent(symbol="NEW", security="New", date_added=None, cik=""),
    ]
    changes = [Change(date(2020, 1, 2), "OLD", "Old", "GONE", "Gone", "rename")]
    sessions = [date(2020, 1, day) for day in range(1, 4)]
    rename = SymbolMapRow("rename", "NEW", "OLD", date(2020, 1, 3), None, "fixture")

    result = reconstruct_membership(
        constituents, changes, sessions, symbol_map=(rename,)
    )
    without = reconstruct_membership(constituents, changes, sessions, symbol_map=())

    assert result.count_min == result.count_max == 2
    assert ("NEW", "OLD", date(2020, 1, 2), date(2020, 1, 2)) in {
        (row.line, row.ticker, row.first, row.last) for row in result.episodes
    }
    assert ("NEW", "NEW", date(2020, 1, 3), date(2020, 1, 3)) in {
        (row.line, row.ticker, row.first, row.last) for row in result.episodes
    }
    assert without.count_max == 3
    assert without.unreconciled[0].ticker == "OLD"


def test_unreconciled_records_are_listed() -> None:
    """S231-A5: unreconciled change records are reported rather than dropped."""
    from scripts.sp500_membership import reconstruct_membership
    from scripts.sp500_wiki import Change, Constituent

    result = reconstruct_membership(
        [Constituent(symbol="KEEP", security="Keep", date_added=None, cik="")],
        [Change(date(2020, 1, 2), "MISSING", "Missing", "GONE", "Gone", "fixture")],
        [date(2020, 1, 1), date(2020, 1, 2)],
        symbol_map=(),
    )

    assert [(row.date, row.ticker, row.reason) for row in result.unreconciled] == [
        (date(2020, 1, 2), "MISSING", "added ticker absent")
    ]
