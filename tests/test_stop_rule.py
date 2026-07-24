"""Shared stop-rule contract tests.

Agent: contracts
Role: verify the cross-agent stop-loss calculation.
External I/O: none.
"""

from __future__ import annotations

from contracts.stop_rule import check_stop


def test_check_stop_is_inclusive_at_threshold() -> None:
    assert check_stop(9500, 10000, 0.05)


def test_check_stop_rejects_prices_above_threshold() -> None:
    assert not check_stop(9501, 10000, 0.05)
