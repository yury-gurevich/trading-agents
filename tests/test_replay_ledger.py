"""Tests for S235 replay ledger edge accounting.

Agent: tooling
Role: verify gap marks, line endings, no-bar expirations, and stop refusals.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from scripts.replay_broker import PendingOrder, ReplayPosition
from scripts.replay_ledger import (
    queue_orders,
    settle_pending,
    settle_stops,
)
from scripts.replay_marks import (
    apply_adjustment_rebases,
    exit_ended_positions,
    mark_positions,
)
from scripts.replay_settings import build_effective_settings
from scripts.sp500_bars import BarRow
from scripts.sp500_guards import KnownMove
from scripts.sp500_membership import Episode

from agents.execution.order_tolerance import OrderToleranceConfig
from contracts.common import Explanation, Money
from contracts.portfolio_manager import OrderIntent


def test_gap_day_marks_at_last_close_without_losing_position_value() -> None:
    """S235-A8: a gap session carries the held line at its last close."""
    line_bars = {
        "AAA": (
            BarRow("AAA", "AAA", date(2020, 1, 2), 100, 100, 100, 100, 10),
            BarRow("AAA", "AAA", date(2020, 1, 6), 110, 110, 110, 110, 10),
        )
    }
    positions = {
        "AAA": ReplayPosition(
            "AAA", 2, 10_000, 9_000, date(2020, 1, 2), date(2020, 1, 3)
        )
    }

    marked = mark_positions(50_000, positions, line_bars, date(2020, 1, 3))

    assert marked.equity_cents == 70_000
    assert marked.long_cents == 20_000
    assert marked.gap_marks == 1
    assert "AAA" in positions


def test_ended_lines_exit_at_last_close_with_reason_and_leave_book() -> None:
    """S235-A8: ended bar series sell once as data_end or membership_end."""
    session = date(2020, 1, 3)
    line_bars = {
        "AAA": (BarRow("AAA", "AAA", session, 10, 10, 10, 10, 10),),
        "BBB": (BarRow("BBB", "BBB", session, 20, 20, 20, 20, 10),),
    }
    positions = {
        "AAA": ReplayPosition("AAA", 1, 1_000, 900, session, session),
        "BBB": ReplayPosition("BBB", 1, 2_000, 1_800, session, session),
    }
    fills: list[dict[str, object]] = []

    result = exit_ended_positions(
        session,
        positions,
        line_bars,
        (
            Episode("AAA", "AAA", date(2020, 1, 1), session),
            Episode("BBB", "BBB", date(2020, 1, 1), date(2020, 1, 6)),
        ),
        fills,
    )

    assert result.cash_delta_cents == 3_000
    assert result.data_end_exits == 1
    assert result.membership_end_exits == 1
    assert {row["reason"] for row in fills} == {"data_end", "membership_end"}
    assert positions == {}


def test_adjustment_error_rebases_and_skips_the_false_jump_stop() -> None:
    """S235-A7: listed adjustment errors rebase entry/stop and book no jump loss."""
    session = date(2020, 1, 3)
    line_bars = {
        "AAA": (
            BarRow("AAA", "AAA", date(2020, 1, 2), 100, 100, 100, 100, 10),
            BarRow("AAA", "AAA", session, 40, 41, 35, 40, 10),
        )
    }
    positions = {
        "AAA": ReplayPosition("AAA", 1, 10_000, 9_000, date(2020, 1, 2), session)
    }
    fills: list[dict[str, object]] = []

    rebased = apply_adjustment_rebases(
        session,
        positions,
        line_bars,
        (KnownMove("AAA", session, "adjustment-error", "fixture"),),
    )
    cash = settle_stops(
        {"AAA": line_bars["AAA"][1]},
        positions,
        fills,
        slippage_bps=0,
        skip_lines=rebased.lines,
    )
    marked = mark_positions(0, positions, line_bars, session)

    assert cash == 0
    assert fills == []
    assert rebased.count == 1
    assert positions["AAA"].entry_price_cents == 4_000
    assert positions["AAA"].stop_price_cents == 3_600
    assert marked.equity_cents == 10_000


def test_pending_order_without_target_bar_expires_as_no_bar() -> None:
    """S235-A4: a DAY order with no target-session bar expires visibly."""
    pending = [PendingOrder("AAA", "buy", 1, 1_000, date(2020, 1, 3), 0.05)]

    result = settle_pending(
        date(2020, 1, 3),
        date(2020, 1, 6),
        pending,
        {},
        {},
        [],
        slippage_bps=0,
    )

    assert result.expired == 1
    assert result.no_bar == 1
    assert result.cash_delta_cents == 0


def test_buy_intent_without_stop_is_refused_not_defaulted() -> None:
    """S235-A4: replay refuses buy intents that lack a PM stop width."""
    pending: list[PendingOrder] = []
    intent = OrderIntent(
        ticker="AAA",
        action="buy",
        quantity=1,
        est_price=Money(amount=Decimal("10")),
        stop_pct=None,
        rationale=Explanation(summary="buy", evidence_refs=("fixture",)),
    )

    refused = queue_orders(
        (intent,),
        (date(2020, 1, 2), date(2020, 1, 3)),
        0,
        pending,
        OrderToleranceConfig.from_settings(build_effective_settings(()).execution),
    )

    assert refused == 1
    assert pending == []
