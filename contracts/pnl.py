"""Shared realized-PnL arithmetic.

Agent: contracts (shared)
Role: keep fill-time PnL math available without cross-agent imports.
External I/O: none.
"""

from __future__ import annotations


def realized_pnl_cents(
    exit_price_cents: int, entry_price_cents: int, quantity: int
) -> int:
    """Gross realized PnL in integer cents for a long position."""
    return (exit_price_cents - entry_price_cents) * quantity
