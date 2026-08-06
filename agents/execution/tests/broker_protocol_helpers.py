"""Broker protocol test helpers.

Agent: execution
Role: keep broker fakes compatible with the Broker port.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from agents.execution.broker import BrokerAccount

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill
    from contracts.common import Money

_DEFAULT_CENTS = 10000000


class NoStopBrokerMixin:
    """Provide stop methods for broker fakes that do not exercise stops."""

    def submit_stop(
        self,
        idempotency_key: str,
        ticker: str,
        side: Literal["buy", "sell"],
        quantity: int,
        stop_price: Money,
        tif: str = "gtc",
    ) -> BrokerFill:
        """Fail loudly if a test unexpectedly places a broker stop."""
        raise AssertionError("test broker should not submit stop orders")

    def cancel(self, broker_order_id: str) -> None:
        """Fail loudly if a test unexpectedly cancels a broker stop."""
        raise AssertionError("test broker should not cancel stop orders")

    def account(self) -> BrokerAccount:
        """Return a deterministic fresh account unless a test overrides it."""
        return BrokerAccount(
            cash_cents=_DEFAULT_CENTS,
            equity_cents=_DEFAULT_CENTS,
            buying_power_cents=_DEFAULT_CENTS,
        )
