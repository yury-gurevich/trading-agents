"""Reporter trade-outcome metric tests.

Agent: reporter
Role: verify dollar-based profit-factor and expectancy over realized close PnL.
External I/O: none.
"""

from __future__ import annotations

from agents.reporter.domain.trade_outcomes import collect_trade_outcomes
from kernel import Node


def _close(key: str, *, trigger: str, pnl_cents: int | None) -> Node:
    props: dict[str, object] = {"position_id": key, "trigger": trigger}
    if pnl_cents is not None:
        props["pnl_cents"] = pnl_cents
    return Node("CloseDecision", f"close:{key}", props)


def test_no_closes_returns_zero_sentinels() -> None:
    outcomes = collect_trade_outcomes(())
    assert "profit_factor" not in outcomes
    assert "expectancy_cents" not in outcomes
    assert outcomes["closed_trades_with_pnl"] == 0.0


def test_time_exits_now_contribute() -> None:
    # A time exit carries real pnl_cents and counts (the % approximation dropped it).
    outcomes = collect_trade_outcomes((_close("a", trigger="time", pnl_cents=300),))
    assert outcomes["closed_trades_with_pnl"] == 1.0
    assert outcomes["expectancy_cents"] == 300.0


def test_only_losses_zero_profit_factor_negative_expectancy() -> None:
    outcomes = collect_trade_outcomes(
        (
            _close("a", trigger="stop", pnl_cents=-500),
            _close("b", trigger="stop", pnl_cents=-300),
        )
    )
    assert outcomes["profit_factor"] == 0.0  # no wins -> denominator-only guard
    assert outcomes["expectancy_cents"] == -400.0
    assert outcomes["closed_trades_with_pnl"] == 2.0


def test_only_wins_guards_zero_denominator() -> None:
    outcomes = collect_trade_outcomes((_close("a", trigger="target", pnl_cents=1000),))
    assert outcomes["profit_factor"] == 0.0  # no losses -> zero-denominator guard
    assert outcomes["expectancy_cents"] == 1000.0


def test_mixed_wins_losses_and_break_even() -> None:
    outcomes = collect_trade_outcomes(
        (
            _close("a", trigger="target", pnl_cents=1000),
            _close("b", trigger="target", pnl_cents=1000),
            _close("c", trigger="stop", pnl_cents=-500),
            _close("d", trigger="time", pnl_cents=0),  # break-even contributes 0
        )
    )
    # wins 2000c, gross loss 500c -> PF 4.0; expectancy (2000-500+0)/4 = 375c.
    assert outcomes["profit_factor"] == 4.0
    assert outcomes["expectancy_cents"] == 375.0
    assert outcomes["closed_trades_with_pnl"] == 4.0


def test_close_without_pnl_is_skipped() -> None:
    # A legacy close (or a non-int value) carries no realized pnl -> not counted.
    outcomes = collect_trade_outcomes(
        (
            _close("a", trigger="stop", pnl_cents=None),
            Node("CloseDecision", "bad", {"pnl_cents": "oops"}),
            _close("c", trigger="target", pnl_cents=800),
        )
    )
    assert outcomes["closed_trades_with_pnl"] == 1.0
    assert outcomes["expectancy_cents"] == 800.0


def test_invalidated_close_pnl_is_skipped() -> None:
    outcomes = collect_trade_outcomes(
        (
            Node(
                "CloseDecision",
                "bad",
                {
                    "position_id": "a",
                    "trigger": "stop",
                    "pnl_cents": -600,
                    "pnl_invalidated_at": "2026-07-23T00:00:00+00:00",
                },
            ),
        )
    )
    assert outcomes == {"closed_trades_with_pnl": 0.0}
