"""S281 fixture runs through the real replay runner and session loop.

Agent: tooling
Role: prove stops-only byte parity and each declared exit end to end.
External I/O: synthetic replay outputs under pytest's external tmp_path only.
"""

from __future__ import annotations

from scripts.replay_exits import STOPS_ONLY, ExitPolicy
from tests.replay_exit_fixtures import SESSIONS, run_fixture


def test_a14_stops_only_and_an_absent_policy_write_the_same_bytes(
    tmp_path, monkeypatch
):
    """S281-A14: four outputs are byte-identical and undeclared exits stay absent."""
    for folder in ("absent", "explicit"):
        (tmp_path / folder).mkdir()
    absent, _, _ = run_fixture(monkeypatch, tmp_path / "absent")
    explicit, _, _ = run_fixture(monkeypatch, tmp_path / "explicit", exits=STOPS_ONLY)
    for name in ("equity.csv", "fills.csv", "sessions.csv", "summary.json"):
        assert (tmp_path / "absent" / "out" / name).read_bytes() == (
            tmp_path / "explicit" / "out" / name
        ).read_bytes()
    assert absent == explicit
    assert "exits" not in absent
    assert absent["absent_inputs"]["sell_without_position"] == 0
    before_appendix = {
        "equity.csv": b"date,equity_cents,long_cents\n"
        b"2024-01-02,10000000,0\n2024-01-03,10000400,20400\n"
        b"2024-01-04,10001600,21600\n2024-01-05,10001400,21400\n",
        "fills.csv": b"date,line,price_cents,quantity,reason,side\n"
        b"2024-01-03,AAA,10000,2,limit,buy\n",
        "sessions.csv": b"approved_buy,approved_sell,candidates,date,expired,"
        b"expired_no_bar,gap_marks,members,recommendations_buy,"
        b"recommendations_hold,recommendations_sell\n"
        b"1,0,0,2024-01-02,0,0,0,1,0,0,0\n"
        b"0,0,0,2024-01-03,0,0,0,1,0,0,0\n"
        b"0,0,0,2024-01-04,0,0,0,1,0,0,0\n"
        b"0,0,0,2024-01-05,0,0,0,1,0,0,0\n",
    }
    for name, expected in before_appendix.items():
        assert (tmp_path / "absent" / "out" / name).read_bytes() == expected
    del absent["absent_inputs"]["sell_without_position"]
    assert absent == {
        "absent_inputs": {
            "adjustment_error_rebases": 0,
            "buy_without_stop": 0,
            "data_end_exits": 0,
            "deliberator": 0,
            "earnings": 0,
            "expired_no_bar": 0,
            "fundamentals": 0,
            "gap_marks": 0,
            "member_sessions_without_sector": 0,
            "membership_end_exits": 0,
            "news": 0,
            "pillars_present": ["technical", "relative_strength"],
            "sentiment": 0,
            "sessions_without_vix": 0,
        },
        "non_default_settings": {
            "ANALYST_STOP_TARGET_MODE": "scaled",
            "EXECUTION_DELIBERATION_GRACE_SECONDS": "1800",
            "EXECUTION_ORDER_PRICE_TOLERANCE_MODE": "scaled",
            "PORTFOLIO_MANAGER_MAX_POSITIONS": "60",
            "PORTFOLIO_MANAGER_MAX_POSITION_PCT": "0.01",
            "SCANNER_CANDIDATE_CAP": "25",
        },
        "performance": {
            "average_exposure_pct": 0.1399857619517008,
            "benchmark_return_pct": 0.9999999999999787,
            "equity_cents": 10001400.0,
            "excess_return_pct": 0.012607164029043716,
            "exposure_matched_return_pct": 0.0013928359709813876,
            "max_drawdown_pct": -0.0019996800511901114,
            "performance_gap_sessions": 0.0,
            "performance_sessions": 3.0,
            "portfolio_return_pct": 0.014000000000025103,
            "rolling_excess_return_pct": 0.012607164029043716,
            "rolling_exposure_matched_return_pct": 0.0013928359709813876,
            "rolling_portfolio_return_pct": 0.014000000000025103,
        },
    }


def test_a15_a_take_profit_sells_on_s2_at_the_target(tmp_path, monkeypatch):
    """S281-A15: the manifest policy reaches the loop and fills the PM's target."""
    summary, fills, _ = run_fixture(
        monkeypatch, tmp_path, exits=ExitPolicy(take_profit=True)
    )
    assert [
        (row["side"], row["date"], row["price_cents"], row["reason"]) for row in fills
    ] == [
        ("buy", SESSIONS[1].isoformat(), "10000", "limit"),
        ("sell", SESSIONS[2].isoformat(), "11000", "target"),
    ]
    assert summary["exits"]["policy"]["take_profit"] is True
    assert summary["exits"]["counts"]["buy_without_target"] == 0


def test_a16_a_one_session_time_exit_sells_at_the_next_open(tmp_path, monkeypatch):
    """S281-A16: count the fill session; the next DAY limit fills at S2's 104 open."""
    summary, fills, _ = run_fixture(
        monkeypatch, tmp_path, exits=ExitPolicy(time_exit_sessions=1)
    )
    assert len(fills) == 2
    assert (fills[1]["date"], fills[1]["price_cents"], fills[1]["reason"]) == (
        SESSIONS[2].isoformat(),
        "10400",
        "time_exit",
    )
    assert summary["exits"]["counts"]["time_exit_orders"] == 1


def test_a18_a_target_beats_the_waiting_time_exit_without_creating_cash(
    tmp_path, monkeypatch
):
    """S281-A18: target settlement leaves the queued sell unheld, counted once."""
    summary, fills, _ = run_fixture(
        monkeypatch, tmp_path, exits=ExitPolicy(take_profit=True, time_exit_sessions=1)
    )
    assert [(row["side"], row["reason"], row["price_cents"]) for row in fills] == [
        ("buy", "limit", "10000"),
        ("sell", "target", "11000"),
    ]
    assert summary["absent_inputs"]["sell_without_position"] == 1
    assert summary["exits"]["counts"]["time_exit_orders"] == 1
    assert (tmp_path / "out" / "equity.csv").read_text(encoding="utf-8").splitlines()[
        -1
    ] == ("2024-01-05,10002000,0")


def test_a19_the_high_raises_a_trailing_stop_on_s2_then_it_sells_on_s3(
    tmp_path, monkeypatch
):
    """S281-A19: the high's new stop cannot fire on its own bar and is raised once."""
    summary, fills, _ = run_fixture(
        monkeypatch, tmp_path, exits=ExitPolicy(trailing_stop=True)
    )
    assert len(fills) == 2
    assert (fills[1]["date"], fills[1]["price_cents"], fills[1]["reason"]) == (
        SESSIONS[3].isoformat(),
        "10545",
        "stop",
    )
    assert summary["exits"]["counts"]["trail_raises"] == 1


def test_a20_a_stop_excludes_the_line_starting_on_its_own_run(tmp_path, monkeypatch):
    """S281-A20: S2's stop removes AAA from S2 and S3, exactly two offered runs."""
    summary, fills, offered = run_fixture(
        monkeypatch,
        tmp_path,
        stopped=True,
        exits=ExitPolicy(reentry_cooldown_sessions=2),
    )
    assert offered == [("AAA",), ("AAA",), (), ()]
    assert [(row["side"], row["date"], row["reason"]) for row in fills] == [
        ("buy", SESSIONS[1].isoformat(), "limit"),
        ("sell", SESSIONS[2].isoformat(), "stop"),
    ]
    assert summary["exits"]["counts"]["cooldown_member_sessions"] == 2
