"""Execution reconciliation logic.

Agent: execution
Role: compare recorded execution fills with broker-known outcomes.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill


def reconcile_fills(
    recorded: tuple[BrokerFill, ...], broker: tuple[BrokerFill, ...]
) -> tuple[int, tuple[str, ...]]:
    """Return matched count and deterministic discrepancy descriptions."""
    recorded_by_key = {fill.idempotency_key: fill for fill in recorded}
    broker_by_key = {fill.idempotency_key: fill for fill in broker}
    discrepancies: list[str] = []
    matched = 0
    for key in sorted(recorded_by_key):
        recorded_fill = recorded_by_key[key]
        broker_fill = broker_by_key.get(key)
        if broker_fill is None:
            discrepancies.append(f"{key}: missing_broker_fill")
        elif _signature(recorded_fill) != _signature(broker_fill):
            discrepancies.append(f"{key}: broker_mismatch")
        else:
            matched += 1
    for key in sorted(set(broker_by_key) - set(recorded_by_key)):
        discrepancies.append(f"{key}: unrecorded_broker_fill")
    return matched, tuple(discrepancies)


def _signature(fill: BrokerFill) -> tuple[object, ...]:
    return (
        fill.ticker,
        fill.side,
        fill.quantity,
        fill.price,
        fill.broker_order_id,
        fill.status,
        fill.reason,
    )
