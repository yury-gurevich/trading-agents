"""Whole-share sizing helpers for Portfolio Manager orders.

Agent: portfolio_manager
Role: compute deterministic order quantities from portfolio value and price.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from decimal import Decimal


def size_quantity(
    *,
    portfolio_value: Decimal,
    max_position_pct: Decimal,
    est_price: Decimal,
) -> int:
    """Floor a position budget divided by estimated price into whole shares."""
    if portfolio_value <= 0 or max_position_pct <= 0 or est_price <= 0:
        return 0
    return int((portfolio_value * max_position_pct) // est_price)
