"""Realized-PnL helper tests.

Agent: monitor
Role: verify gross integer-cents realized PnL (win / loss / break-even / multi-share).
External I/O: none.
"""

from __future__ import annotations

from agents.monitor.domain.exit_rules import realized_pnl_cents


def test_realized_pnl_is_positive_above_entry() -> None:
    assert realized_pnl_cents(11100, 10000, 1) == 1100


def test_realized_pnl_is_negative_below_entry() -> None:
    assert realized_pnl_cents(9400, 10000, 1) == -600


def test_realized_pnl_is_zero_at_break_even() -> None:
    assert realized_pnl_cents(10000, 10000, 7) == 0


def test_realized_pnl_scales_with_quantity() -> None:
    # +500c per share over 3 shares -> +1500c.
    assert realized_pnl_cents(10500, 10000, 3) == 1500
    # -250c per share over 4 shares -> -1000c.
    assert realized_pnl_cents(9750, 10000, 4) == -1000


def test_realized_pnl_is_exact_integer_cents() -> None:
    result = realized_pnl_cents(12345, 10000, 6)
    assert result == 14070
    assert isinstance(result, int)
