"""Execution test helpers.

Agent: execution
Role: provide deterministic execution fixtures and bus wiring.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.execution import ExecutionAgent
from agents.execution.broker import PaperBroker
from contracts.common import Explanation, Money, Provenance
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from kernel import AgentMessage, CollectingFaultSink, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from contracts.monitor import CloseDecisionSet


def wire(
    broker: PaperBroker | None = None,
) -> tuple[InProcessBus, InMemoryGraphStore, PaperBroker, CollectingFaultSink]:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    paper = broker or PaperBroker()
    ExecutionAgent(bus, graph=graph, broker=paper, sink=sink).bind()
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


def close_message(payload: CloseDecisionSet) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="execution",
        message_type="request",
        capability="execute_close",
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
    return sum(1 for label, _key in graph._nodes if label == "Fill")
