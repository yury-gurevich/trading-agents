"""Reporter trade-outcome metric tests.

Agent: reporter
Role: verify profit-factor and expectancy over paired Position + CloseDecision nodes.
External I/O: none.
"""

from __future__ import annotations

from agents.reporter.domain.trade_outcomes import (
    _implied_pnl_pct,
    collect_trade_outcomes,
)
from kernel import Node


def _position(key: str, *, stop_pct: float = 0.05, target_pct: float = 0.10) -> Node:
    return Node("Position", key, {"stop_pct": stop_pct, "target_pct": target_pct})


def _close(position_key: str, trigger: str) -> Node:
    return Node(
        "CloseDecision",
        f"close:{position_key}",
        {"position_id": position_key, "trigger": trigger},
    )


def test_implied_pnl_signs_by_trigger() -> None:
    position = _position("p", stop_pct=0.05, target_pct=0.10)
    assert _implied_pnl_pct(position, _close("p", "stop")) == -0.05
    assert _implied_pnl_pct(position, _close("p", "target")) == 0.10
    assert _implied_pnl_pct(position, _close("p", "time")) is None


def test_no_closes_returns_zero_sentinels() -> None:
    outcomes = collect_trade_outcomes((_position("p"),), ())
    assert outcomes["profit_factor"] == 0.0
    assert outcomes["expectancy_pct"] == 0.0
    assert outcomes["closed_trades_with_pnl"] == 0.0


def test_time_exits_are_excluded() -> None:
    outcomes = collect_trade_outcomes((_position("p"),), (_close("p", "time"),))
    assert outcomes["closed_trades_with_pnl"] == 0.0
    assert outcomes["profit_factor"] == 0.0


def test_only_losses_zero_profit_factor_negative_expectancy() -> None:
    outcomes = collect_trade_outcomes(
        (_position("a", stop_pct=0.05), _position("b", stop_pct=0.05)),
        (_close("a", "stop"), _close("b", "stop")),
    )
    assert outcomes["profit_factor"] == 0.0  # no wins -> denominator-only -> guard
    assert outcomes["expectancy_pct"] < 0.0
    assert outcomes["closed_trades_with_pnl"] == 2.0


def test_only_wins_guards_zero_denominator() -> None:
    outcomes = collect_trade_outcomes(
        (_position("a", target_pct=0.10),), (_close("a", "target"),)
    )
    assert outcomes["profit_factor"] == 0.0  # no losses -> zero-denominator guard
    assert outcomes["expectancy_pct"] == 0.10
    assert outcomes["closed_trades_with_pnl"] == 1.0


def test_mixed_two_wins_one_loss() -> None:
    positions = (
        _position("a", target_pct=0.10),
        _position("b", target_pct=0.10),
        _position("c", stop_pct=0.05),
    )
    closes = (
        _close("a", "target"),
        _close("b", "target"),
        _close("c", "stop"),
    )
    outcomes = collect_trade_outcomes(positions, closes)
    # wins sum = 0.20, loss sum = 0.05 -> 4.0
    assert outcomes["profit_factor"] == 4.0
    assert outcomes["expectancy_pct"] == (0.10 + 0.10 - 0.05) / 3
    assert outcomes["closed_trades_with_pnl"] == 3.0


def test_bad_pct_props_never_raise() -> None:
    bad = Node("Position", "p", {"stop_pct": "bad", "target_pct": None})
    outcomes = collect_trade_outcomes((bad,), (_close("p", "stop"),))
    assert outcomes["expectancy_pct"] == 0.0
    assert outcomes["closed_trades_with_pnl"] == 1.0


def test_close_without_position_id_is_skipped() -> None:
    orphan = Node("CloseDecision", "orphan", {"trigger": "stop"})
    outcomes = collect_trade_outcomes((_position("p"),), (orphan,))
    assert outcomes["closed_trades_with_pnl"] == 0.0


def test_open_position_without_close_is_skipped() -> None:
    outcomes = collect_trade_outcomes(
        (_position("a", target_pct=0.10), _position("b")),
        (_close("a", "target"),),
    )
    assert outcomes["closed_trades_with_pnl"] == 1.0
    assert outcomes["expectancy_pct"] == 0.10
