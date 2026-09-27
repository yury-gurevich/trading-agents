"""Tests for S235 script-local replay broker accounting.

Agent: tooling
Role: verify next-session DAY limits, slippage, stops, and adjustment rebasing.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

from scripts.replay_broker import (
    PendingOrder,
    ReplayBar,
    ReplayPosition,
    apply_adjustment_rebase,
    simulate_limit_fill,
    simulate_stop_fill,
)


def test_buy_limit_waits_for_next_session_and_expires_on_gap() -> None:
    """S235-A4: DAY buys fill only on target session when low touches the limit."""
    order = PendingOrder("AAA", "buy", 3, 1_000, date(2020, 1, 3))
    prior = ReplayBar("AAA", date(2020, 1, 2), 900, 1_100, 900, 1_050, 100)
    gapped = ReplayBar("AAA", date(2020, 1, 3), 1_200, 1_300, 1_100, 1_250, 100)

    assert simulate_limit_fill(order, prior, slippage_bps=10) is None
    assert simulate_limit_fill(order, gapped, slippage_bps=10) is None

    touched = ReplayBar("AAA", date(2020, 1, 3), 990, 1_050, 980, 1_020, 100)
    fill = simulate_limit_fill(order, touched, slippage_bps=10)
    assert fill is not None
    assert fill.price_cents == 991


def test_stop_arms_after_fill_session_and_rebases_without_jump_fill() -> None:
    """S235-A5: stops activate later and adjustment days rescale entry plus stop."""
    position = ReplayPosition(
        "AAA",
        2,
        entry_price_cents=1_000,
        stop_price_cents=900,
        opened=date(2020, 1, 3),
        stop_active_from=date(2020, 1, 6),
    )
    fill_day = ReplayBar("AAA", date(2020, 1, 3), 890, 950, 880, 910, 100)
    stop_day = ReplayBar("AAA", date(2020, 1, 6), 920, 930, 880, 890, 100)

    assert simulate_stop_fill(position, fill_day, slippage_bps=10) is None
    fill = simulate_stop_fill(position, stop_day, slippage_bps=10)
    assert fill is not None
    assert fill.price_cents == 899

    rebased = apply_adjustment_rebase(position, ratio=0.5)
    assert (rebased.entry_price_cents, rebased.stop_price_cents) == (500, 450)
