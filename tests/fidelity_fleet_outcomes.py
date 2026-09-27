"""Deliberation, execution and fill outcomes written by the fleet's own writers.

Agent: tooling
Role: give a fleet-produced PM run its live downstream facts for Layer 3 and the export.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from agents.deliberator.store import write_deliberation_run
from agents.execution.broker import BrokerFill
from agents.execution.domain.orders import execution_run_id
from agents.execution.drop_sweep_records import record_drop
from agents.execution.reconciliation_store import refresh_pending_fills
from agents.execution.store import write_fills
from contracts.common import Money
from contracts.portfolio_manager import OrderIntentSet
from kernel import CollectingFaultSink

if TYPE_CHECKING:
    from kernel import GraphStore, Node

Outcome = Literal["filled", "rejected", "dropped", "pending"]


def deliberate(graph: GraphStore, pm: Node, verdicts: dict[str, str]) -> Node:
    """Record a DeliberationRun; only `overturn` enters vetoed_tickers (DLIB-OUT-02)."""
    order_set = OrderIntentSet.model_validate(pm.props["order_intent_set"])
    return write_deliberation_run(
        graph,
        pm,
        order_set=order_set,
        verdicts=verdicts,
        vetoed_tickers=[t for t, v in sorted(verdicts.items()) if v == "overturn"],
        debates={},
        narrative="fixture",
        transcript=[],
        role_models={},
        max_rounds=1,
        real_debate_count=len(verdicts),
        failed_open_count=0,
        orphaned_reply_count=0,
        failed_open_tickers=[],
        failed_open_reason="",
        llm_call_keys=[],
    )


def execute(graph: GraphStore, pm: Node, outcomes: dict[str, Outcome]) -> Node:
    """Submit the named approvals and settle each as the broker would report it."""
    order_set = OrderIntentSet.model_validate(pm.props["order_intent_set"])
    run_id = execution_run_id("submit", order_set.run_id)
    submitted = tuple(
        _fill(
            order_set.run_id, intent.ticker, intent.action, intent.quantity, "pending"
        )
        for intent in order_set.approved
        if intent.ticker in outcomes
    )
    write_fills(graph, run_id=run_id, fills=submitted, order_set=order_set)
    execution = graph.merge_node(
        "ExecutionRun",
        run_id,
        {
            "source_pm_run_id": order_set.run_id,
            "submitted": len(submitted),
            "rejected": 0,
            "skipped": len(order_set.approved) - len(submitted),
            "deliberation_status": "applied",
            "deliberation_posture": "binding",
            "deliberation_blocked_count": 0,
        },
    )
    graph.add_edge(pm, execution, "EXECUTED_BY")
    sink = CollectingFaultSink()
    terminal = tuple(
        _fill(order_set.run_id, fill.ticker, fill.side, fill.quantity, outcome)
        for fill in submitted
        if (outcome := outcomes[fill.ticker]) in ("filled", "rejected")
    )
    refresh_pending_fills(graph, terminal, sink)
    for fill in submitted:
        if outcomes[fill.ticker] == "dropped":
            node = graph.get_node("Fill", fill.idempotency_key)
            record_drop(graph, sink, fill, node, "expired")
    return execution


def _fill(
    pm_run_id: str, ticker: str, action: str, quantity: int, status: str
) -> BrokerFill:
    side: Literal["buy", "sell"] = "sell" if action == "sell" else "buy"
    return BrokerFill(
        idempotency_key=f"{pm_run_id}:{ticker}:{side}",
        ticker=ticker,
        side=side,
        quantity=quantity,
        price=Money(amount=50),
        broker_order_id=f"broker-{pm_run_id}-{ticker}",
        status=status,  # type: ignore[arg-type]
        submitted_at="2026-09-28T22:45:00+00:00",
    )
