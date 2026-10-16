"""Script-local broker simulator for S235 replay orders.

Agent: tooling
Role: simulate DAY limit orders, GTC protective stops and take-profits, and rebases.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from contracts.stop_rule import PCT_SCALE

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
    stop_pct: float = 0.0
    target_pct: float | None = None
    reason: str = "limit"


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
    price_scale: float = 1.0
    target_price_cents: int | None = None
    stop_pct: float = 0.0


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
        order.reason,
    )


def simulate_stop_fill(
    position: ReplayPosition, bar: ReplayBar, *, slippage_bps: int
) -> ReplayFill | None:
    """Fill an active stop, or a take-profit when the position carries one.

    From the activation session on: an open at or above the target fills the target at
    the open; a low at or below the stop fills the stop at min(open, stop), so a bar
    touching both counts as the stop (EXP-011's and S241's rule); a high at or above
    the target fills it at the target.
    """
    if bar.date < position.stop_active_from:
        return None
    target = position.target_price_cents
    if target is not None and bar.open_cents >= target:
        return _exit_fill(position, bar, bar.open_cents, "target", slippage_bps)
    if bar.low_cents <= position.stop_price_cents:
        price = min(bar.open_cents, position.stop_price_cents)
        return _exit_fill(position, bar, price, "stop", slippage_bps)
    if target is not None and bar.high_cents >= target:
        return _exit_fill(position, bar, target, "target", slippage_bps)
    return None


def _exit_fill(
    position: ReplayPosition,
    bar: ReplayBar,
    price_cents: int,
    reason: str,
    slippage_bps: int,
) -> ReplayFill:
    return ReplayFill(
        bar.date,
        position.line,
        "sell",
        position.quantity,
        _apply_slippage(price_cents, "sell", slippage_bps),
        reason,
    )


def apply_adjustment_rebase(
    position: ReplayPosition, *, ratio: float
) -> ReplayPosition:
    """Rescale a held line's entry and stop for an adjustment-error day."""
    if ratio <= 0:
        return position
    target = position.target_price_cents
    return replace(
        position,
        entry_price_cents=round(position.entry_price_cents * ratio),
        stop_price_cents=round(position.stop_price_cents * ratio),
        price_scale=position.price_scale / ratio,
        target_price_cents=None if target is None else round(target * ratio),
    )


def target_price_cents(entry_cents: int, target_pct: float | None) -> int | None:
    """The take-profit price, rounded up to the cent; None without a target."""
    if target_pct is None:
        return None
    scale = PCT_SCALE + round(target_pct * PCT_SCALE)
    return -(-entry_cents * scale // PCT_SCALE)


def _apply_slippage(price_cents: int, side: str, slippage_bps: int) -> int:
    factor = (
        1.0 + slippage_bps / 10_000 if side == "buy" else 1.0 - slippage_bps / 10_000
    )
    return round(price_cents * factor)
