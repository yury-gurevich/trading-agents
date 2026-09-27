"""Ledger helpers for S235 replay broker fills.

Agent: tooling
Role: queue PM intents, settle orders/stops, and value replay positions.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal, NamedTuple

from scripts.replay_broker import (
    PendingOrder,
    ReplayBar,
    ReplayFill,
    ReplayPosition,
    simulate_limit_fill,
    simulate_stop_fill,
)
from scripts.replay_marks import mark_positions

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


class PendingSettlement(NamedTuple):
    expired: int
    cash_delta_cents: int
    no_bar: int


def queue_orders(
    intents: tuple[Any, ...],
    sessions: tuple[date, ...],
    index: int,
    pending: list[PendingOrder],
    config: OrderToleranceConfig,
) -> int:
    if index + 1 >= len(sessions):
        return 0
    buy_without_stop = 0
    for intent in intents:
        side: Literal["buy", "sell"] = "buy" if intent.action == "buy" else "sell"
        if side == "buy" and intent.stop_pct is None:
            buy_without_stop += 1
            continue
        evidence = resolve_order_tolerance(intent, side, config)
        pending.append(
            PendingOrder(
                intent.ticker,
                side,
                intent.quantity,
                money_cents(evidence.applied_limit_price),
                sessions[index + 1],
                intent.stop_pct if intent.stop_pct is not None else 0.0,
            )
        )
    return buy_without_stop


def settle_stops(
    bars: dict[str, BarRow],
    positions: dict[str, ReplayPosition],
    fills: list[dict[str, Any]],
    slippage_bps: int,
    skip_lines: frozenset[str] = frozenset(),
) -> int:
    cash = 0
    for line, position in tuple(positions.items()):
        if line in skip_lines:
            continue
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
        price_cents = _position_price_cents(position, fill.price_cents)
        fills.append(_fill_row(fill, price_cents=price_cents))
        cash += fill.quantity * price_cents
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
) -> PendingSettlement:
    expired = no_bar = cash = 0
    for order in tuple(pending):
        row = bars.get(order.line)
        if order.target_session != session:
            continue
        if row is None:
            expired += 1
            no_bar += 1
            continue
        fill = simulate_limit_fill(order, replay_bar(row), slippage_bps=slippage_bps)
        if fill is None:
            expired += 1
            continue
        if fill.side == "buy":
            fills.append(_fill_row(fill))
            cash -= fill.quantity * fill.price_cents
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
            position = positions.get(fill.line)
            price_cents = (
                fill.price_cents
                if position is None
                else _position_price_cents(position, fill.price_cents)
            )
            fills.append(_fill_row(fill, price_cents=price_cents))
            cash += fill.quantity * price_cents
            positions.pop(fill.line, None)
    return PendingSettlement(expired, cash, no_bar)


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
    cash_cents: int,
    positions: dict[str, ReplayPosition],
    line_bars: dict[str, tuple[BarRow, ...]],
    session: date,
) -> int:
    return mark_positions(cash_cents, positions, line_bars, session).equity_cents


def next_session(sessions: tuple[date, ...], index: int) -> date:
    return sessions[index + 1] if index + 1 < len(sessions) else sessions[index]


def money_cents(value: Money) -> int:
    return int((value.amount * _CENTS).quantize(Decimal("1")))


def _fill_row(fill: ReplayFill, *, price_cents: int | None = None) -> dict[str, Any]:
    row = fill.__dict__ | {"date": fill.date.isoformat()}
    if price_cents is not None:
        row["price_cents"] = price_cents
    return row


def _position_price_cents(position: ReplayPosition, price_cents: int) -> int:
    return round(price_cents * position.price_scale)
