"""Pure monitor exit rules.

Agent: monitor
Role: observe whether an open position has crossed its stop floor.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from contracts.pnl import realized_pnl_cents as realized_pnl_cents
from contracts.stop_rule import check_stop

Observation = Literal["stop_breached", "clear"]
Trigger = Literal["stop", "none"]


@dataclass(frozen=True)
class ExitPosition:
    """Position fields needed by the exit-rule evaluator."""

    opened_price_cents: int
    stop_pct: float


def evaluate_position(
    position: ExitPosition, current_price_cents: int
) -> tuple[Observation, Trigger]:
    """Evaluate the stop floor without authoring an exit decision."""
    if check_stop(current_price_cents, position.opened_price_cents, position.stop_pct):
        return "stop_breached", "stop"
    return "clear", "none"
