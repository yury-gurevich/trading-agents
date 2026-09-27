"""Script-local broker simulator for S235 replay orders.

Agent: tooling
Role: simulate DAY limit orders, GTC protective stops, and replay ledger rebases.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

STOP_ACTIVATES_SESSION_AFTER_FILL = "session_after_fill"


@dataclass(frozen=True)
class ReplayBar:
    line: str
    date: date
    open_cents: int
    high_cents: int
    low_cents: int
    close_cents: int
    volume: int


@dataclass(frozen=True)
class PendingOrder:
    line: str
    side: str
    quantity: int
    limit_cents: int
    target_session: date
    stop_pct: float = 0.05


@dataclass(frozen=True)
class ReplayFill:
    date: date
    line: str
    side: str
    quantity: int
    price_cents: int
    reason: str


@dataclass(frozen=True)
class ReplayPosition:
    line: str
    quantity: int
    entry_price_cents: int
    stop_price_cents: int
    opened: date
    stop_active_from: date
    position_ref: str = ""


def simulate_limit_fill(
    order: PendingOrder, bar: ReplayBar, *, slippage_bps: int
) -> ReplayFill | None:
    """Fill a DAY limit only on its target session and only if touched."""
    if bar.date != order.target_session:
        return None
    if order.side == "buy":
        if bar.low_cents > order.limit_cents:
            return None
        price = min(bar.open_cents, order.limit_cents)
    else:
        if bar.high_cents < order.limit_cents:
            return None
        price = max(bar.open_cents, order.limit_cents)
    return ReplayFill(
        bar.date,
        order.line,
        order.side,
        order.quantity,
        _apply_slippage(price, order.side, slippage_bps),
        "limit",
    )


def simulate_stop_fill(
    position: ReplayPosition, bar: ReplayBar, *, slippage_bps: int
) -> ReplayFill | None:
    """Fill an active stop at min(open, stop), after the activation session."""
    if (
        bar.date < position.stop_active_from
        or bar.low_cents > position.stop_price_cents
    ):
        return None
    price = min(bar.open_cents, position.stop_price_cents)
    return ReplayFill(
        bar.date,
        position.line,
        "sell",
        position.quantity,
        _apply_slippage(price, "sell", slippage_bps),
        "stop",
    )


def apply_adjustment_rebase(
    position: ReplayPosition, *, ratio: float
) -> ReplayPosition:
    """Rescale a held line's entry and stop for an adjustment-error day."""
    return ReplayPosition(
        position.line,
        position.quantity,
        round(position.entry_price_cents * ratio),
        round(position.stop_price_cents * ratio),
        position.opened,
        position.stop_active_from,
        position.position_ref,
    )


def _apply_slippage(price_cents: int, side: str, slippage_bps: int) -> int:
    factor = (
        1.0 + slippage_bps / 10_000 if side == "buy" else 1.0 - slippage_bps / 10_000
    )
    return round(price_cents * factor)
