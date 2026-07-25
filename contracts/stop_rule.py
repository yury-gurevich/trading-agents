"""Shared stop-loss rule.

Agent: contracts
Role: expose the downside floor calculation across agent boundaries.
External I/O: none.
"""

from __future__ import annotations

PCT_SCALE = 10000


def stop_price_cents(opened_price_cents: int, stop_pct: float) -> int:
    """Return the integer-cent stop threshold for an opened position."""
    return opened_price_cents * (PCT_SCALE - round(stop_pct * PCT_SCALE)) // PCT_SCALE


def check_stop(
    current_price_cents: int, opened_price_cents: int, stop_pct: float
) -> bool:
    """Return whether current price is at or below the stop threshold."""
    return current_price_cents <= stop_price_cents(opened_price_cents, stop_pct)
