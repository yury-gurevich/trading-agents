"""Broker-stop test fixtures.

Agent: execution
Role: share graph and broker fixtures for broker-native stop tests.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from agents.execution.broker import BrokerFill
from contracts.common import Explanation, Money, Provenance
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from contracts.positions import PositionStopThreshold
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from agents.execution.broker import BrokerPosition
    from kernel import GraphStore, Node


@dataclass
class TrackingBroker:
    """Broker fixture with explicit fills/positions and cancel recording."""

    broker_fills: tuple[BrokerFill, ...] = ()
    broker_positions: tuple[BrokerPosition, ...] = ()
    cancelled: list[str] = field(default_factory=list)

    def submit(
        self,
        idempotency_key: str,
        ticker: str,
        side: Literal["buy", "sell"],
        quantity: int,
        limit_price: Money,
        tolerance_bps: int | None = None,
    ) -> BrokerFill:
        raise AssertionError("test PM run should not submit market orders")

    def submit_stop(
        self,
        idempotency_key: str,
        ticker: str,
        side: Literal["buy", "sell"],
        quantity: int,
        stop_price: Money,
        tif: str = "gtc",
    ) -> BrokerFill:
        raise AssertionError("test should not place new stops")

    def cancel(self, broker_order_id: str) -> None:
        self.cancelled.append(broker_order_id)

    def fills(self) -> tuple[BrokerFill, ...]:
        return self.broker_fills

    def positions(self) -> tuple[BrokerPosition, ...]:
        return self.broker_positions


def seed_pm_run(graph: InMemoryGraphStore, payload: OrderIntentSet) -> Node:
    """Write a PMRun carrying its OrderIntentSet payload."""
    return graph.merge_node(
        "PMRun", payload.run_id, {"order_intent_set": payload.model_dump(mode="json")}
    )


def order_set(run_id: str, *orders: OrderIntent) -> OrderIntentSet:
    """Return a PM result fixture."""
    return OrderIntentSet(
        run_id=run_id,
        approved=orders,
        rejected=(),
        explanation=Explanation(summary="fixture PM result"),
        provenance=Provenance(
            run_id=run_id,
            source_agent="portfolio_manager",
            graph_node_id=f"PMRun:{run_id}",
        ),
    )


def sell(ticker: str, quantity: int, position_ref: str) -> OrderIntent:
    """Return a sell intent for one held position_ref."""
    return OrderIntent(
        ticker=ticker,
        action="sell",
        quantity=quantity,
        est_price=Money(amount=Decimal("100.00")),
        position_ref=position_ref,
        rationale=Explanation(summary="fixture sell"),
    )


def position(
    graph: GraphStore,
    key: str,
    ticker: str,
    quantity: int,
    *,
    opened_price_cents: int,
) -> None:
    """Write one active Position node."""
    graph.merge_node(
        "Position",
        key,
        {
            "run_id": "seed",
            "ticker": ticker,
            "quantity": quantity,
            "opened_price_cents": opened_price_cents,
            "stop_pct": 0.05,
            "target_pct": 0.10,
            "horizon_days": 10,
            "opened_at": "2026-07-20",
            "status": "open",
        },
    )


def stop_threshold(
    ticker: str, position_ref: str, quantity: int
) -> PositionStopThreshold:
    """Return one broker-stop threshold fixture."""
    return PositionStopThreshold(
        ticker=ticker,
        quantity=quantity,
        position_ref=position_ref,
        opened_price_cents=10000,
        stop_pct=0.05,
    )


class RuntimeStopBroker(TrackingBroker):
    def submit_stop(
        self,
        idempotency_key: str,
        ticker: str,
        side: Literal["buy", "sell"],
        quantity: int,
        stop_price: Money,
        tif: str = "gtc",
    ) -> BrokerFill:
        raise RuntimeError("broker offline")


class CancelRaisesBroker(TrackingBroker):
    def cancel(self, broker_order_id: str) -> None:
        raise RuntimeError("cancel failed")


class PendingStopBroker(TrackingBroker):
    def __init__(self) -> None:
        super().__init__()
        self.submitted: list[str] = []

    def submit_stop(
        self,
        idempotency_key: str,
        ticker: str,
        side: Literal["buy", "sell"],
        quantity: int,
        stop_price: Money,
        tif: str = "gtc",
    ) -> BrokerFill:
        self.submitted.append(idempotency_key)
        return BrokerFill(
            idempotency_key=idempotency_key,
            ticker=ticker,
            side=side,
            quantity=quantity,
            price=stop_price,
            broker_order_id=f"broker:{idempotency_key}",
            status="pending",
        )


class VanishingPositionGraph(InMemoryGraphStore):
    def __init__(self) -> None:
        super().__init__()
        self.position_reads = 0
        self.hide_after_position_reads = 999

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        nodes = super().list_nodes(label)
        if label != "Position":
            return nodes
        self.position_reads += 1
        if self.position_reads >= self.hide_after_position_reads:
            return ()
        return nodes
