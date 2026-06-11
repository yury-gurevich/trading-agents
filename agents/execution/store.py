"""Execution graph write path.

Agent: execution
Role: write fills, reconciliation outcomes, and OrderIntent lineage.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from contracts.common import Money, Provenance

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill
    from contracts.execution import ExecutionStage
    from contracts.portfolio_manager import OrderIntentSet
    from kernel import GraphStore, Node

CENTS_PER_DOLLAR = Decimal("100")
STAGES: tuple[ExecutionStage, ...] = (
    "paper",
    "broker_shadow",
    "live_manual",
    "live_autopilot",
)


def write_fills(
    graph: GraphStore,
    *,
    run_id: str,
    fills: tuple[BrokerFill, ...],
    order_set: OrderIntentSet | None = None,
) -> Provenance:
    """Write idempotency-keyed fills and optional PM order lineage."""
    first: Node | None = None
    pm_run_key = _pm_run_key(order_set)
    for fill in fills:
        node = graph.merge_node(
            "Fill",
            fill.idempotency_key,
            {
                "ticker": fill.ticker,
                "side": fill.side,
                "quantity": fill.quantity,
                "price_cents": _money_to_cents(fill.price),
                "price_currency": fill.price.currency,
                "broker_order_id": fill.broker_order_id,
                "status": fill.status,
                "reason": fill.reason,
            },
        )
        first = node if first is None else first
        _link_order_intent(graph, node, pm_run_key, fill.ticker)
    return Provenance(
        run_id=run_id,
        source_agent="execution",
        graph_node_id=None if first is None else f"{first.label}:{first.key}",
    )


def write_reconciliation(
    graph: GraphStore,
    *,
    matched: int,
    discrepancies: tuple[str, ...],
) -> Provenance:
    """Write one reconciliation outcome node."""
    run_id = f"reconciliation-{uuid.uuid4().hex}"
    node = graph.merge_node(
        "Reconciliation",
        run_id,
        {
            "matched": matched,
            "discrepancy_count": len(discrepancies),
            "discrepancies": list(discrepancies),
            "created_at": datetime.now(tz=UTC).isoformat(),
        },
    )
    return Provenance(
        run_id=run_id,
        source_agent="execution",
        graph_node_id=f"{node.label}:{node.key}",
    )


def write_stage_transition(
    graph: GraphStore,
    *,
    from_stage: str,
    to_stage: str,
    reason: str,
) -> Node:
    """Append one immutable StageTransition node."""
    transitioned_at = datetime.now(tz=UTC).isoformat()
    return graph.merge_node(
        "StageTransition",
        f"stage:{to_stage}:{transitioned_at}",
        {
            "from_stage": from_stage,
            "to_stage": to_stage,
            "reason": reason,
            "transitioned_at": transitioned_at,
        },
    )


def current_stage_from_graph(
    graph: GraphStore, default: ExecutionStage
) -> ExecutionStage:
    """Return the latest graph-authored stage, or the configured fallback."""
    transitions = graph.list_nodes("StageTransition")
    if not transitions:
        return default
    latest = max(
        transitions, key=lambda node: str(node.props.get("transitioned_at", ""))
    )
    value = str(latest.props.get("to_stage", default))
    return value if value in STAGES else default


def _money_to_cents(money: Money) -> int:
    cents = (money.amount * CENTS_PER_DOLLAR).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(cents)


def _pm_run_key(order_set: OrderIntentSet | None) -> str | None:
    if order_set is None:
        return None
    graph_id = order_set.provenance.graph_node_id
    if graph_id is None or not graph_id.startswith("PMRun:"):
        return None
    return graph_id.split(":", 1)[1]


def _link_order_intent(
    graph: GraphStore, fill: Node, pm_run_key: str | None, ticker: str
) -> None:
    if pm_run_key is None:
        return
    order = graph.get_node("OrderIntent", f"{pm_run_key}:{ticker}")
    if order is not None:
        graph.add_edge(fill, order, "EXECUTES")
