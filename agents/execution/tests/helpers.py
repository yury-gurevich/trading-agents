"""Execution test helpers.

Agent: execution
Role: provide deterministic execution fixtures and bus wiring.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from agents.execution import ExecutionAgent
from agents.execution.broker import BrokerFill, BrokerPosition
from agents.execution.paper_broker import PaperBroker
from agents.execution.tests.broker_protocol_helpers import NoStopBrokerMixin
from agents.execution.tests.stage_helpers import flag_handler
from contracts.common import Explanation, Money, Provenance
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from kernel import AgentMessage, CollectingFaultSink, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from agents.execution.settings import ExecutionSettings


def wire(
    broker: PaperBroker | None = None,
    settings: ExecutionSettings | None = None,
) -> tuple[InProcessBus, InMemoryGraphStore, PaperBroker, CollectingFaultSink]:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    paper = broker or PaperBroker()
    bus.register("supervisor", "flag_for_human", flag_handler(graph))
    ExecutionAgent(bus, graph=graph, broker=paper, settings=settings, sink=sink).bind()
    return bus, graph, paper, sink


def order(ticker: str, *, price: str = "100.00") -> OrderIntent:
    return OrderIntent(
        ticker=ticker,
        action="buy",
        quantity=1,
        est_price=Money(amount=Decimal(price)),
        rationale=Explanation(summary="fixture order"),
    )


def order_set(*orders: OrderIntent) -> OrderIntentSet:
    return OrderIntentSet(
        run_id="pm-run-fixture",
        approved=orders,
        rejected=(),
        explanation=Explanation(summary="fixture PM result"),
        provenance=Provenance(
            run_id="pm-run-fixture",
            source_agent="portfolio_manager",
            graph_node_id="PMRun:pm-run-fixture",
        ),
    )


def seed_order_nodes(graph: InMemoryGraphStore, payload: OrderIntentSet) -> None:
    graph.merge_node("PMRun", payload.run_id, {"approved_count": len(payload.approved)})
    for item in payload.approved:
        graph.merge_node(
            "OrderIntent",
            f"{payload.run_id}:{item.ticker}",
            {"ticker": item.ticker},
        )


def submit_message(payload: OrderIntentSet) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="execution",
        message_type="request",
        capability="submit",
        payload=payload.model_dump(mode="json"),
    )


def reconcile_message() -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="execution",
        message_type="request",
        capability="reconcile",
        payload={"run_id": "reconcile-test"},
    )


def stage_status_message() -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="execution",
        message_type="request",
        capability="stage_status",
        payload={},
    )


def fill_node_count(graph: InMemoryGraphStore) -> int:
    return len(graph.list_nodes("Fill"))


class PositionBroker(NoStopBrokerMixin):
    """Broker fake that returns configured positions."""

    def __init__(self, positions: tuple[BrokerPosition, ...]) -> None:
        self._positions = positions

    def positions(self) -> tuple[BrokerPosition, ...]:
        return self._positions

    def fills(self) -> tuple[BrokerFill, ...]:
        return ()

    def submit(
        self,
        idempotency_key: str,
        ticker: str,
        side: Literal["buy", "sell"],
        quantity: int,
        limit_price: Money,
        tolerance_bps: int | None = None,
    ) -> BrokerFill:
        raise AssertionError("position-sync test should not submit orders")


class FailingBroker(PositionBroker):
    """Broker fake that always fails the positions read."""

    def __init__(self) -> None:
        super().__init__(())

    def positions(self) -> tuple[BrokerPosition, ...]:
        raise RuntimeError("broker unavailable")


class FailFirstBroker(PositionBroker):
    """Broker fake that fails once, then returns a healthy book."""

    def __init__(self) -> None:
        super().__init__((BrokerPosition("AAPL", 3, 10000, 30000),))
        self.calls = 0

    def positions(self) -> tuple[BrokerPosition, ...]:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("first run poisoned")
        return super().positions()
