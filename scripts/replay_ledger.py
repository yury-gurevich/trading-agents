"""Ledger helpers for S235 replay broker fills.

Agent: tooling
Role: queue PM intents, settle orders/stops, and value replay positions.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal

from scripts.replay_broker import (
    PendingOrder,
    ReplayBar,
    ReplayPosition,
    simulate_limit_fill,
    simulate_stop_fill,
)

from agents.execution.order_tolerance import (
    OrderToleranceConfig,
    resolve_order_tolerance,
)
from contracts.stop_rule import stop_price_cents

if TYPE_CHECKING:
    from datetime import date

    from scripts.sp500_bars import BarRow

    from contracts.common import Money

_CENTS = Decimal("100")


def queue_orders(
    intents: tuple[Any, ...],
    sessions: tuple[date, ...],
    index: int,
    pending: list[PendingOrder],
    config: OrderToleranceConfig,
) -> None:
    if index + 1 >= len(sessions):
        return
    for intent in intents:
        side: Literal["buy", "sell"] = "buy" if intent.action == "buy" else "sell"
        evidence = resolve_order_tolerance(intent, side, config)
        pending.append(
            PendingOrder(
                intent.ticker,
                side,
                intent.quantity,
                money_cents(evidence.applied_limit_price),
                sessions[index + 1],
                intent.stop_pct or 0.05,
            )
        )


def settle_stops(
    bars: dict[str, BarRow],
    positions: dict[str, ReplayPosition],
    fills: list[dict[str, Any]],
    slippage_bps: int,
) -> int:
    cash = 0
    for line, position in tuple(positions.items()):
        row = bars.get(line)
        fill = (
            None
            if row is None
            else simulate_stop_fill(
                position, replay_bar(row), slippage_bps=slippage_bps
            )
        )
        if fill is None:
            continue
        fills.append(fill.__dict__ | {"date": fill.date.isoformat()})
        cash += fill.quantity * fill.price_cents
        positions.pop(line, None)
    return cash


def settle_pending(
    session: date,
    next_session: date,
    pending: list[PendingOrder],
    bars: dict[str, BarRow],
    positions: dict[str, ReplayPosition],
    fills: list[dict[str, Any]],
    slippage_bps: int,
) -> tuple[int, int]:
    expired = cash = 0
    for order in tuple(pending):
        row = bars.get(order.line)
        if row is None or order.target_session != session:
            continue
        fill = simulate_limit_fill(order, replay_bar(row), slippage_bps=slippage_bps)
        if fill is None:
            expired += 1
            continue
        fills.append(fill.__dict__ | {"date": fill.date.isoformat()})
        cash += (-1 if fill.side == "buy" else 1) * fill.quantity * fill.price_cents
        if fill.side == "buy":
            positions[fill.line] = ReplayPosition(
                fill.line,
                fill.quantity,
                fill.price_cents,
                stop_price_cents(fill.price_cents, order.stop_pct),
                session,
                next_session,
                f"{fill.line}-{session.isoformat()}",
            )
        else:
            positions.pop(fill.line, None)
    return expired, cash


def replay_bar(row: BarRow) -> ReplayBar:
    return ReplayBar(
        row.line,
        row.date,
        round(row.open * 100),
        round(row.high * 100),
        round(row.low * 100),
        round(row.close * 100),
        row.volume,
    )


def equity_cents(
    cash_cents: int, positions: dict[str, ReplayPosition], bars: dict[str, BarRow]
) -> int:
    return cash_cents + sum(
        pos.quantity * round(bars[line].close * 100)
        for line, pos in positions.items()
        if line in bars
    )


def next_session(sessions: tuple[date, ...], index: int) -> date:
    return sessions[index + 1] if index + 1 < len(sessions) else sessions[index]


def money_cents(value: Money) -> int:
    return int((value.amount * _CENTS).quantize(Decimal("1")))
