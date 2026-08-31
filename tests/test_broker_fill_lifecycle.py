"""Broker Fill lifecycle contract tests.

Agent: contracts
Role: keep resting-stop Fills distinct from open broker orders.
External I/O: none.
"""

from __future__ import annotations

import importlib

from kernel import Node


def test_resting_stop_fill_is_not_an_open_order_fill() -> None:
    """EXEC-OBS-05: resting stops and open orders are distinct populations."""
    lifecycle = importlib.import_module("contracts.broker_lifecycle")
    fill = Node(
        "Fill",
        "stop:held-ref:MSFT",
        {
            "ticker": "MSFT",
            "side": "sell",
            "status": "pending",
            "broker_order_id": "broker-msft",
            "stop_order_key": "stop:held-ref:MSFT",
        },
    )

    assert lifecycle.is_resting_stop_fill(fill) is True
    assert lifecycle.is_open_order_fill(fill) is False


def test_pending_buy_fill_is_an_open_order_fill() -> None:
    """EXEC-OBS-05: pending non-stop Fill remains open order evidence."""
    lifecycle = importlib.import_module("contracts.broker_lifecycle")
    fill = Node(
        "Fill",
        "sched-2026-08-28:MSFT:buy",
        {
            "ticker": "MSFT",
            "side": "buy",
            "status": "pending",
            "broker_order_id": "broker-msft",
        },
    )

    assert lifecycle.is_resting_stop_fill(fill) is False
    assert lifecycle.is_open_order_fill(fill) is True


def test_terminal_and_dropped_fills_are_not_open_order_fills() -> None:
    """EXEC-OBS-05: terminal or dropped order Fills are not open."""
    lifecycle = importlib.import_module("contracts.broker_lifecycle")

    assert (
        lifecycle.is_open_order_fill(
            Node(
                "Fill",
                "run:AAPL:buy",
                {"status": "pending", "broker_status": "filled"},
            )
        )
        is False
    )
    assert (
        lifecycle.is_open_order_fill(
            Node(
                "Fill",
                "run:MSFT:buy",
                {"status": "pending", "drop_reason": "unfilled at session end"},
            )
        )
        is False
    )
    assert (
        lifecycle.is_open_order_fill(
            Node("Position", "held:AAPL", {"status": "pending"})
        )
        is False
    )


def test_drop_terminal_statuses_are_named_lifecycle_vocabulary() -> None:
    """EXEC-OBS-05: drop terminal reasons live in broker_lifecycle."""
    lifecycle = importlib.import_module("contracts.broker_lifecycle")

    assert lifecycle.is_resolved_drop_status("canceled") is True
    assert lifecycle.is_resolved_drop_status("expired") is True
    assert lifecycle.is_resolved_drop_status("filled") is False
