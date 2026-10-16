"""S281 policy validation and session-local bookkeeping tests.

Agent: tooling
Role: prove policy defaults, trailing stops, cool-downs and time-exit guards.
External I/O: none.
"""

from __future__ import annotations

import pytest
from scripts.replay_broker import PendingOrder
from scripts.replay_exits import (
    STOPS_ONLY,
    ExitPolicy,
    ExitState,
    exit_policy_from,
    held_sessions,
)
from tests.replay_exit_fixtures import CONFIG, SESSIONS, bar, intent, position


def test_a1_defaults_are_stops_only_and_bad_policy_values_are_refused():
    """S281-A1: absent policy is undeclared; keys, booleans and counts are checked."""
    assert exit_policy_from(None) is STOPS_ONLY
    assert exit_policy_from({}) == STOPS_ONLY
    assert not STOPS_ONLY.declared
    assert STOPS_ONLY.as_dict() == {
        "take_profit": False,
        "time_exit_sessions": None,
        "trailing_stop": False,
        "reentry_cooldown_sessions": 0,
    }
    bad = [{"unknown": True}, {"take_profit": "yes"}, {"trailing_stop": "yes"}]
    bad += [{"time_exit_sessions": value} for value in (0, True, 1.5, -1)]
    bad += [{"reentry_cooldown_sessions": value} for value in (True, 1.5, -1)]
    for data in bad:
        with pytest.raises(ValueError, match=r"unknown exit keys|must be"):
            exit_policy_from(data)
    assert exit_policy_from({"time_exit_sessions": 1}).declared


def test_a8_a_trailing_stop_rises_from_the_active_high_and_never_falls():
    """S281-A8: only active positions trail their high, with one counted raise."""
    positions = {
        "AAA": position(),
        "BBB": position("BBB", opened=SESSIONS[2], stop_active_from=SESSIONS[3]),
        "CCC": position("CCC"),
    }
    original = positions.copy()
    rows = {line: bar(line=line, prices=(100, 110, 99, 100)) for line in ("AAA", "BBB")}
    state = ExitState(ExitPolicy(trailing_stop=True))
    state.raise_stops(SESSIONS[2], positions, rows)
    assert positions["AAA"].stop_price_cents == 10_450
    assert positions["BBB"] == original["BBB"]
    assert positions["CCC"] == original["CCC"]
    state.raise_stops(SESSIONS[2], positions, {"AAA": bar(prices=(100, 102, 99, 100))})
    assert positions["AAA"].stop_price_cents == 10_450
    assert state.counts["trail_raises"] == 1
    stopped = ExitState(STOPS_ONLY)
    stopped.raise_stops(SESSIONS[2], original, rows)
    assert original["AAA"].stop_price_cents == 9_500
    assert not stopped.counts


def test_a9_only_a_stop_excludes_its_line_for_exactly_k_runs():
    """S281-A9: the stop's own run counts first; targets never start a cool-down."""
    fills = [
        {"line": "AAA", "reason": "stop"},
        {"line": "BBB", "reason": "target"},
        {"line": "CCC", "reason": "time_exit"},
    ]
    state = ExitState(ExitPolicy(reentry_cooldown_sessions=2))
    state.note_stops(fills)
    members = ("AAA", "BBB", "CCC")
    assert state.cool(members) == ("BBB", "CCC")
    assert state.cool(members) == ("BBB", "CCC")
    assert state.cool(members) == members
    assert state.counts["cooldown_member_sessions"] == 2
    disabled = ExitState(STOPS_ONLY)
    disabled.note_stops(fills)
    assert disabled.cool(members) == members
    assert disabled.cooling == {}
    assert disabled.counts["cooldown_member_sessions"] == 0


def test_a10_the_fill_session_is_the_first_held_session():
    """S281-A10: a fill on S0 has closed one, two, three and four sessions."""
    assert [held_sessions(SESSIONS, SESSIONS[0], i) for i in range(4)] == [1, 2, 3, 4]


def test_a11_time_exits_respect_age_waiting_sells_bars_and_the_last_session():
    """S281-A11: only a due holding queues a next-session sell; last means no count."""
    positions = {line: position(line) for line in ("AAA", "BBB", "CCC")}
    positions["DDD"] = position("DDD", opened=SESSIONS[1])
    pending = [PendingOrder("BBB", "sell", 2, 10_000, SESSIONS[2])]
    rows = {
        line: bar(1, line=line, prices=(100, 103, 99, 102))
        for line in ("AAA", "BBB", "DDD")
    }
    state = ExitState(ExitPolicy(time_exit_sessions=2))
    assert state.queue_orders(1, SESSIONS, positions, pending, rows, (), CONFIG) == 0
    assert len(pending) == 2
    order = pending[1]
    assert (order.line, order.side, order.quantity, order.target_session) == (
        "AAA",
        "sell",
        2,
        SESSIONS[2],
    )
    assert (order.limit_cents, order.reason) == (10_149, "time_exit")
    assert state.counts["time_exit_orders"] == 1
    pending.clear()
    state.queue_orders(2, SESSIONS, positions, pending, rows, (), CONFIG)
    assert [order.line for order in pending] == ["AAA", "BBB", "DDD"]
    assert state.counts["time_exit_orders"] == 4
    last = ExitState(ExitPolicy(time_exit_sessions=1))
    pending.clear()
    last.queue_orders(3, SESSIONS, positions, pending, rows, (), CONFIG)
    assert pending == []
    assert last.counts["time_exit_orders"] == 0


def test_a12_a_targetless_stopped_buy_is_counted_only_under_take_profit():
    """S281-A12: count only buys with a stop but no target, and wire take_profit."""
    approved = (
        intent(target_pct=None),
        intent(stop_pct=None, target_pct=None),
        intent("sell", target_pct=None),
        intent(),
    )
    state = ExitState(ExitPolicy(take_profit=True))
    pending = []
    assert state.queue_orders(0, SESSIONS, {}, pending, {}, approved, CONFIG) == 1
    assert state.counts["buy_without_target"] == 1
    assert [order.target_pct for order in pending] == [None, None, 0.1]
    disabled = ExitState(STOPS_ONLY)
    disabled.queue_orders(0, SESSIONS, {}, [], {}, approved, CONFIG)
    assert disabled.counts["buy_without_target"] == 0


def test_a13_summary_is_absent_unless_declared_and_names_every_count():
    """S281-A13: policy and all four literal count keys appear only when declared."""
    assert ExitState(STOPS_ONLY).summary() is None
    state = ExitState(ExitPolicy(time_exit_sessions=1))
    state.queue_orders(
        1, SESSIONS, {"AAA": position()}, [], {"AAA": bar(1)}, (), CONFIG
    )
    assert state.summary() == {
        "counts": {
            "buy_without_target": 0,
            "cooldown_member_sessions": 0,
            "time_exit_orders": 1,
            "trail_raises": 0,
        },
        "policy": {
            "take_profit": False,
            "time_exit_sessions": 1,
            "trailing_stop": False,
            "reentry_cooldown_sessions": 0,
        },
    }
