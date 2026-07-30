"""Drop-sweep test fixtures.

Agent: execution
Role: seed pending Fill lineage and broker fakes for ADR-0018 tests.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from agents.execution.broker import BrokerFill
from agents.execution.tests.broker_stop_helpers import TrackingBroker
from contracts.common import Explanation, Money
from contracts.portfolio_manager import OrderIntent

if TYPE_CHECKING:
    from kernel import InMemoryGraphStore


class SelectiveCancelBroker(TrackingBroker):
    """Broker fake that fails one configured cancellation."""

    def __init__(
        self, *, broker_fills: tuple[BrokerFill, ...], fail_order_id: str
    ) -> None:
        super().__init__(broker_fills=broker_fills)
        self.fail_order_id = fail_order_id

    def cancel(self, broker_order_id: str) -> None:
        if broker_order_id == self.fail_order_id:
            raise RuntimeError("already filled")
        super().cancel(broker_order_id)


class TrackingSubmitBroker(TrackingBroker):
    """Broker fake that accepts ordinary submissions for replay tests."""

    def submit(
        self,
        idempotency_key: str,
        ticker: str,
        side: Literal["buy", "sell"],
        quantity: int,
        limit_price: Money,
        tolerance_bps: int | None = None,
    ) -> BrokerFill:
        return BrokerFill(
            idempotency_key,
            ticker,
            side,
            quantity,
            limit_price,
            f"paper:{idempotency_key}",
            "filled",
        )


def seed_fill_lineage(
    graph: InMemoryGraphStore, run_id: str, key: str, ticker: str
) -> None:
    """Seed PMRun -> ExecutionRun lineage for one pending Fill."""
    pm_run = graph.merge_node("PMRun", run_id, {"approved_count": 1})
    order = graph.merge_node("OrderIntent", f"{run_id}:{ticker}", {"ticker": ticker})
    fill = graph.merge_node(
        "Fill",
        key,
        {
            "ticker": ticker,
            "side": "buy",
            "quantity": 1,
            "price_cents": 10000,
            "price_currency": "USD",
            "broker_order_id": f"broker:{key}",
            "status": "pending",
            "source_run_id": run_id,
            "broker_idempotency_key": key,
            "attempt_ordinal": 0,
        },
    )
    execution = graph.merge_node("ExecutionRun", f"execution-submit-{run_id}", {})
    graph.add_edge(fill, order, "EXECUTES")
    graph.add_edge(order, pm_run, "EMITTED_BY")
    graph.add_edge(pm_run, execution, "EXECUTED_BY")


def broker_order(
    key: str,
    ticker: str,
    *,
    side: Literal["buy", "sell"] = "buy",
    status: Literal["filled", "partial", "rejected", "pending"] = "pending",
    reason: str | None = None,
    order_type: str = "limit",
) -> BrokerFill:
    """Return one broker order fixture."""
    return BrokerFill(
        key,
        ticker,
        side,
        1,
        Money(amount=Decimal("100.00")),
        f"broker:{key}",
        status,
        reason,
        order_type=order_type,
        time_in_force="day",
    )


def stop_fact(
    graph: InMemoryGraphStore, key: str, ticker: str, broker_order_id: str
) -> None:
    """Seed an active BrokerStopOrder fact."""
    graph.merge_node(
        "BrokerStopOrder",
        key,
        {
            "ticker": ticker,
            "position_ref": key,
            "stop_price_cents": 9500,
            "broker_order_id": broker_order_id,
            "placed_at": "2026-07-29T00:00:00+00:00",
        },
    )


def sell(ticker: str, position_ref: str) -> OrderIntent:
    """Return one sell intent for a held position."""
    return OrderIntent(
        ticker=ticker,
        action="sell",
        quantity=3,
        est_price=Money(amount=Decimal("100.00")),
        position_ref=position_ref,
        rationale=Explanation(summary="forced exit"),
    )
