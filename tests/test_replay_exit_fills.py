"""S281 exit barrier and ledger tests.

Agent: tooling
Role: prove literal barrier prices, order reasons, target propagation and cash.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import replace

from scripts.replay_broker import (
    PendingOrder,
    apply_adjustment_rebase,
    simulate_limit_fill,
    simulate_stop_fill,
    target_price_cents,
)
from scripts.replay_ledger import queue_orders, replay_bar, settle_pending
from tests.replay_exit_fixtures import CONFIG, SESSIONS, bar, intent, position


def test_a2_the_open_then_stop_then_target_decides_the_fill():
    """S281-A2: the open wins first, otherwise both touched means the stop."""
    held = position(target_price_cents=11_000)
    cases = (
        ((112, 115, 94, 110), (11_200, "target")),
        ((100, 111, 94, 105), (9_500, "stop")),
        ((104, 113, 100, 108), (11_000, "target")),
        ((93, 111, 90, 100), (9_300, "stop")),
    )
    for prices, expected in cases:
        fill = simulate_stop_fill(held, replay_bar(bar(prices=prices)), slippage_bps=0)
        assert fill is not None
        assert (fill.price_cents, fill.reason) == expected
        assert (fill.line, fill.quantity, fill.side, fill.date) == (
            "AAA",
            2,
            "sell",
            SESSIONS[2],
        )


def test_a3_a_position_without_a_target_keeps_the_stop_rule():
    """S281-A3: no target, no early activation, and stop slippage is preserved."""
    held = position(stop_active_from=SESSIONS[2])
    assert (
        simulate_stop_fill(
            held, replay_bar(bar(prices=(104, 120, 96, 108))), slippage_bps=100
        )
        is None
    )
    assert (
        simulate_stop_fill(
            held, replay_bar(bar(1, prices=(90, 120, 89, 100))), slippage_bps=100
        )
        is None
    )
    for opened, expected in ((100, 9_405), (93, 9_207)):
        fill = simulate_stop_fill(
            held, replay_bar(bar(prices=(opened, 110, 90, 100))), slippage_bps=100
        )
        assert fill is not None
        assert (fill.price_cents, fill.reason) == (expected, "stop")


def test_a4_the_target_rounds_up_and_rebases_with_the_stop():
    """S281-A4: 100.01 plus ten percent is 110.02 and rebase scales both barriers."""
    assert target_price_cents(10_001, 0.10) == 11_002
    assert target_price_cents(10_001, None) is None
    held = position(entry_price_cents=10_001, target_price_cents=11_002)
    rebased = apply_adjustment_rebase(held, ratio=0.5)
    assert rebased == replace(
        held,
        entry_price_cents=5_000,
        stop_price_cents=4_750,
        target_price_cents=5_501,
        price_scale=2.0,
    )
    assert rebased.stop_pct == 0.05
    assert apply_adjustment_rebase(held, ratio=0) == held
    assert apply_adjustment_rebase(position(), ratio=0.5).target_price_cents is None


def test_a5_a_limit_fill_retains_its_orders_reason():
    """S281-A5: a queued time exit stays attributed and ordinary limits stay limit."""
    for reason in ("time_exit", "limit"):
        order = PendingOrder("AAA", "sell", 2, 10_000, SESSIONS[2])
        if reason == "time_exit":
            order = replace(order, reason=reason)
        fill = simulate_limit_fill(order, replay_bar(bar()), slippage_bps=0)
        assert fill is not None
        assert (fill.price_cents, fill.reason) == (10_400, reason)


def test_a6_only_an_opted_in_buy_carries_a_target():
    """S281-A6: take_profit carries the buy target, never a sell target."""
    for enabled, expected in ((False, [None, None]), (True, [0.1, None])):
        pending = []
        assert (
            queue_orders(
                (intent(), intent("sell")),
                SESSIONS,
                0,
                pending,
                CONFIG,
                take_profit=enabled,
            )
            == 0
        )
        assert [order.target_pct for order in pending] == expected
        assert [order.side for order in pending] == ["buy", "sell"]
        assert [order.target_session for order in pending] == [SESSIONS[1]] * 2


def test_a7_a_buy_opens_its_barriers_and_an_unheld_sell_credits_nothing():
    """S281-A7: record stop_pct and target; an unheld sell credits nothing."""
    pending = [
        PendingOrder("AAA", "buy", 2, 10_050, SESSIONS[1], 0.05, 0.1),
        PendingOrder("BBB", "sell", 9, 9_000, SESSIONS[1]),
    ]
    positions, fills = {}, []
    result = settle_pending(
        SESSIONS[1],
        SESSIONS[2],
        pending,
        {"AAA": bar(1, prices=(100, 102, 99, 102)), "BBB": bar(1, line="BBB")},
        positions,
        fills,
        slippage_bps=0,
    )
    assert result.sell_without_position == 1
    assert (result.cash_delta_cents, result.expired, result.no_bar) == (-20_000, 0, 0)
    assert len(fills) == 1
    assert (fills[0]["line"], fills[0]["side"]) == ("AAA", "buy")
    assert set(positions) == {"AAA"}
    held = positions["AAA"]
    assert (held.entry_price_cents, held.stop_price_cents, held.target_price_cents) == (
        10_000,
        9_500,
        11_000,
    )
    assert (held.stop_pct, held.opened, held.stop_active_from) == (
        0.05,
        SESSIONS[1],
        SESSIONS[2],
    )
