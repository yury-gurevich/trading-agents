"""S282: FIFO round trips and reason profiles from replay fills.

Agent: tooling
Role: prove line-specific pairing, held sessions and annualised buy counts.
External I/O: local temporary fills.csv only.
"""

from datetime import date
from pathlib import Path

import pytest
from scripts.exit_verdict_trips import exit_profile, profile_of
from tests.exit_verdict_fixtures import trip_rows, write_rows
from tests.replay_verdict_fixtures import trading_days


def test_a13_sells_close_oldest_buy_of_their_line() -> None:
    """S282-A13: FIFO, pair-count years, strictly positive gains and sorted reasons."""
    days = trading_days(date(2017, 1, 3), 253)
    profile = profile_of(trip_rows(days), days)
    assert {
        key: profile[key] for key in ("buys", "trips", "unmatched_sells", "open_at_end")
    } == {
        "buys": 5,
        "trips": 4,
        "unmatched_sells": 1,
        "open_at_end": 1,
    }
    assert profile["buys_per_year"] == 5
    exits = profile["exits"]
    assert list(exits) == ["stop", "take_profit", "time_exit"]
    assert exits["stop"] == pytest.approx(
        {
            "count": 1,
            "gain_share_pct": 0,
            "mean_return_pct": -10,
            "median_held_sessions": 2,
        }
    )
    assert exits["take_profit"] == pytest.approx(
        {
            "count": 2,
            "gain_share_pct": 100,
            "mean_return_pct": 10,
            "median_held_sessions": 9,
        }
    )
    assert exits["time_exit"] == {
        "count": 1,
        "gain_share_pct": 0,
        "mean_return_pct": 0,
        "median_held_sessions": 10,
    }


def test_a14_csv_profile_matches_rows_and_unknown_date_raises(tmp_path: Path) -> None:
    """S282-A14: file parsing preserves the profile and rejects a non-session date."""
    days = trading_days(date(2017, 1, 3), 253)
    rows, path = trip_rows(days), tmp_path / "fills.csv"
    write_rows(path, rows)
    assert exit_profile(path, days) == profile_of(rows, days)
    rows[0]["date"] = "2016-12-31"
    write_rows(path, rows)
    with pytest.raises(KeyError):
        exit_profile(path, days)
