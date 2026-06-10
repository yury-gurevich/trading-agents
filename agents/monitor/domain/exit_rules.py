"""Pure monitor exit rules.

Agent: monitor
Role: decide whether an open position should close under deterministic rules.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

Decision = Literal["close", "hold"]
Trigger = Literal["stop", "target", "time", "none"]
PCT_SCALE = 10000


@dataclass(frozen=True)
class ExitPosition:
    """Position fields needed by the exit-rule evaluator."""

    opened_price_cents: int
    opened_at: str
    stop_pct: float
    target_pct: float
    horizon_days: int


def check_stop(
    current_price_cents: int, opened_price_cents: int, stop_pct: float
) -> bool:
    """Return whether current price is at or below the stop threshold."""
    threshold = opened_price_cents * (PCT_SCALE - round(stop_pct * PCT_SCALE))
    return current_price_cents * PCT_SCALE <= threshold


def check_target(
    current_price_cents: int, opened_price_cents: int, target_pct: float
) -> bool:
    """Return whether current price is at or above the target threshold."""
    threshold = opened_price_cents * (PCT_SCALE + round(target_pct * PCT_SCALE))
    return current_price_cents * PCT_SCALE >= threshold


def check_time(opened_at_iso: str, default_horizon_days: int, today: date) -> bool:
    """Return whether the configured holding horizon has elapsed."""
    opened_at = datetime.fromisoformat(opened_at_iso).date()
    return (today - opened_at).days >= default_horizon_days


def evaluate_position(
    position: ExitPosition, current_price_cents: int, today: date
) -> tuple[Decision, Trigger]:
    """Evaluate stop, target, then time in deterministic priority order."""
    if check_stop(current_price_cents, position.opened_price_cents, position.stop_pct):
        return "close", "stop"
    if check_target(
        current_price_cents, position.opened_price_cents, position.target_pct
    ):
        return "close", "target"
    if check_time(position.opened_at, position.horizon_days, today):
        return "close", "time"
    return "hold", "none"
