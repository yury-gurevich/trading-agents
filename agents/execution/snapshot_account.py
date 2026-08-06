"""Account properties for execution-owned run-start snapshots.

Agent: execution
Role: convert broker account facts into BrokerPositionSnapshot properties.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.execution.broker import BrokerAccount


def account_snapshot_props(
    account: BrokerAccount | None, stale_reason: str | None
) -> dict[str, object]:
    """Return account props for a BrokerPositionSnapshot."""
    if account is None:
        props: dict[str, object] = {"account_status": "stale"}
        if stale_reason:
            props["account_stale_reason"] = stale_reason
        return props
    return {
        "account_status": "fresh",
        "account_cash_cents": account.cash_cents,
        "account_equity_cents": account.equity_cents,
        "account_buying_power_cents": account.buying_power_cents,
    }
